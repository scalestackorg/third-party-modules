# Developer Guide for Third-Party Module Integration

This guide provides detailed steps for developing, deploying, and registering modules on the Scalestack platform using this repository's automated CI/CD pipeline.

## Overview

This repository is configured with GitHub Actions to automatically deploy your modules to staging when you create a pull request to the main branch. The deployment process is streamlined:

1. **Develop your module** in a feature branch
2. **Create a PR to main** - automatically triggers deployment to staging
3. **Test in staging** environment
4. **Register your module** in the Scalestack workbench
5. **Merge to main** when ready

The platform uses an Orchestrator Service with Amazon SQS to queue module execution commands, dispatched via Amazon SNS to individual module queues. The `scalestack_sdk` library simplifies input/output handling for modules.

## Quick Start

### Prerequisites
1. Clone this repository and create a new feature branch:
```bash
git clone <repository-url>
cd third-party-modules
git checkout -b feature/team-name/module-name
```

2. Ensure Poetry is installed and the project is initialized:
```bash
poetry install
```

## 1. Developing a Module in This Repository

### Dynamic Team Structure

This repository uses a **fully dynamic team-based organization**. Simply create a directory with the pattern `modules_<teamname>/` and the CDK automatically creates a stack for your team!

```
third-party-modules/
└── modules_<teamname>/  # Your team's directory (auto-detected)
    └── your_module/     # Your module
        └── index.py     # Module code
```

### Creating Your Module

1. **Create your team directory** (if it doesn't exist):
```bash
# Choose a team name and create the directory
mkdir modules_yourteam/
```

**No CDK changes needed!** The system automatically detects and deploys your team.

2. **Create your module within your team's directory**:
```bash
mkdir modules_yourteam/my_module_name
touch modules_yourteam/my_module_name/index.py
```

3. **The module will use the repository's shared Poetry environment** with `scalestack_sdk` pre-configured.

### Write the Module

1. Define a `main` function in `index.py` with the `@decorators.aws` decorator from `scalestack_sdk`.
2. Include `**kwargs` as a parameter and return a dictionary.

#### Example (Simple)
```python
from scalestack_sdk import decorators

@decorators.aws
def main(email: str, **kwargs):
    return {"url": "https://www.linkedin.com/in/apollo"}
```

#### Example (Realistic, using Apollo API)
```python
import requests
from scalestack_sdk import decorators
from pydantic import SecretStr
from structlog.stdlib import get_logger

APOLLO_URL = "https://api.apollo.io/v1/people/match"
HEADERS = {"Content-Type": "application/json"}
logger = get_logger()

@decorators.aws(default_secret="APOLLO_API_KEY")
def main(email: str, api_key: SecretStr, **kwargs):
    response = requests.post(
        APOLLO_URL,
        headers=HEADERS,
        json={"email": email, "api_key": api_key.get_secret_value()},
    )
    response.raise_for_status()
    data = response.json()
    person = data.get("person", {})
    linkedin_url = person.get("linkedin_url")
    if not linkedin_url:
        logger.warning("No LinkedIn URL found", email=email)
    return {"linkedin_url": linkedin_url}
```

#### Notes
- Use `SecretStr` for API keys to prevent leakage (`api_key.get_secret_value()` for plain text).
- Use `structlog` for structured logging.
- The `@decorators.aws` handles SQS batch processing and maps inputs/outputs to the database.
- **Important: Type Conversion** - Always convert input types explicitly with error handling. Inputs from the workflow might arrive as a different type to what you expect. Add type conversion with try-except blocks at the beginning of your function:
  ```python
  @decorators.aws
  def main(max_results: int, timeout: float, **kwargs):
      # Convert to ensure correct types with error handling
      try:
          max_results = int(max_results) if not isinstance(max_results, int) else max_results
      except (ValueError, TypeError):
          return {"processed": "Invalid max_results value"}
      
      try:
          timeout = float(timeout) if not isinstance(timeout, float) else timeout
      except (ValueError, TypeError):
          return {"processed": "Invalid timeout value"}
      
      # Your module logic here
      return {"processed": max_results}
  ```

### Add Module-Specific Dependencies

If your module needs additional dependencies beyond what's in the main `pyproject.toml`:

1. **Add to the main Poetry project**:
```bash
poetry add <package-name>
```

2. **The GitHub Actions workflow will automatically export requirements.txt** for each module when you create a PR.

Note: The `requirements.txt` file is auto-generated during deployment - you don't need to create it manually.

### Example: Complex Module

For a module with multiple inputs (e.g., fetching news):

```python
from scalestack_sdk import decorators
from typing import Dict, List, Any, Literal

@decorators.aws
def main(
    company_name: str,
    time_range: int,
    max_quantity: int,
    target_words: List[str],
    banned_words: List[str],
    news_api: Literal["bing-api", "serpapi-google-news"] = "bing-api",
    **kwargs
) -> Dict[str, Any]:
    # Module's body
    return {"relevant_news": parsed_news, "news_score": news_score}
```

## 2. Deploying Your Module

Deployment happens automatically through GitHub Actions when you create a pull request to the main branch.

### Dynamic Team Stack Deployment

Each team automatically gets their own CloudFormation stack - no configuration needed!

1. **Create your team directory** with pattern `modules_<teamname>/`
2. **Add modules to your directory**
3. **Create a PR** - CDK automatically:
   - Detects your team directory
   - Creates a stack for your team
   - Deploys all modules in your directory

### How It Works

The dynamic CDK system (`cdk_dynamic_stacks.py`):
- Scans for all `modules_*` directories
- Creates a separate stack for each team found
- Deploys shared infrastructure first
- Then deploys each team's modules in their own stack
- Automatically handles all configuration and tagging

### Starting a New Team

Just create your directory and go!

```bash
# Example: Data team starting fresh
mkdir modules_data/
mkdir modules_data/etl_pipeline/
echo "# ETL code" > modules_data/etl_pipeline/index.py
# Commit, push, create PR - Done!
```

### Deployment Steps

1. **Commit your module** to your feature branch:
```bash
git add modules_yourteam/my_module_name/
git commit -m "[YourTeam] Add new module: my_module_name"
git push origin feature/team-name/module-name
```

2. **Create a Pull Request** to the main branch on GitHub.

### Automated Deployment Process

When you create or update a PR:

1. **GitHub Actions automatically**:
   - Sets up the Python environment
   - Installs all dependencies
   - Exports requirements.txt for each module
   - Runs CDK synth to validate the stack
   - Deploys to AWS staging environment (`newstg`)
   - Comments on your PR with deployment status

2. **Monitor deployment**:
   - Check the Actions tab in GitHub for progress
   - Review the PR comment for deployment confirmation
   - If deployment fails, check the logs for errors

### Testing Your Module Locally

Before deploying, create a `test.py` file to test your module locally. This should be a copy of your main module code but without the Scalestack-specific decorators and libraries:

```python
# test.py
# Copy your main function here WITHOUT the @decorators.aws decorator
# and WITHOUT from scalestack_sdk import decorators
import requests  # Keep regular imports
# Remove: from scalestack_sdk import decorators

def main(email: str, api_key: str, **kwargs):
    # Your actual module logic here
    response = requests.post(
        "https://api.example.com/endpoint",
        json={"email": email, "api_key": api_key}
    )
    return {"result": response.json()}

if __name__ == "__main__":
    result = main(
        email="test@example.com",
        api_key="test_key"
    )
    print("Module output:", result)
```

Run the test:
```bash
python test.py
```

### Manual Deployment (Optional)

If you need to deploy manually without creating a PR:

1. **Set environment variables**:
```bash
export STAGE="newstg"
export AWS_REGION="us-east-1"
```

2. **Run CDK deploy**:
```bash
poetry run cdk deploy --all
```

Note: Manual deployment requires AWS credentials configured locally. The automated GitHub Actions deployment is recommended.

## 3. Registering Your Deployed Module

After your module is successfully deployed to staging via the GitHub Actions pipeline, register it for frontend integration.

### JSON Structure

Create a JSON file to define the module’s UI components and backend integration.

#### Example (Job Posting Module)
```python
{
  "module_id": "job_posting_enrichment",
  "lambda_name": "modules-jobposting_newstg_job_posting", # Format: modules-{team}_{stage}_{module_name}
  "category": "enrich",
  "label": "Get Job Postings",
  "description": "Find relevant jobs related to a company",
  "api_key_required": True,
  "parameters": {
    "enrichment_inputs": [
      {
        "id": "company_name",
        "component": "dropdown",
        "label": "Company name"
      }
    ],
    "user_inputs": [
      {
        "id": "time_range",
        "component": "dropdown",
        "label": "Time range",
        "options": [
          { "value": "all", "label": "All" },
          { "value": "month", "label": "Last month" },
          { "value": "3 days", "label": "Last 3 days" },
          { "value": "today", "label": "Today" }
        ]
      },
      {
        "id": "max_quantity",
        "component": "dropdown",
        "label": "Max quantity",
        "options": [
          { "value": 999, "label": "All jobs" },
          { "value": 30, "label": "30 jobs" },
          { "value": 20, "label": "20 jobs" },
          { "value": 10, "label": "10 jobs" },
          { "value": 5, "label": "5 jobs" },
          { "value": 4, "label": "4 jobs" },
          { "value": 3, "label": "3 jobs" },
          { "value": 2, "label": "2 jobs" },
          { "value": 1, "label": "1 job" }
        ]
      },
      {
        "id": "remote_only_jobs",
        "component": "dropdown",
        "label": "Remote jobs only",
        "options": [
          { "value": true, "label": "True" },
          { "value": false, "label": "False" }
        ]
      },
      {
        "id": "query",
        "component": "code_editor",
        "label": "Query",
        "placeholder": "Write your query. Insert variables using '/'.",
        "autocomplete_suggestions": true,
        "height": "200px",
        "optional": true
      },
      {
        "id": "job_types",
        "component": "multi_select_dropdown",
        "label": "Job types",
        "optional": true,
        "options": [
          { "value": "FULLTIME", "label": "Full-time" },
          { "value": "CONTRACTOR", "label": "Contractor" },
          { "value": "PARTTIME", "label": "Part-time" },
          { "value": "INTERN", "label": "Intern" }
        ]
      },
      {
        "id": "job_titles",
        "component": "tags",
        "label": "Job titles",
        "optional": true
      }
    ],
    "outputs": {
      "component": "checkbox_field_list",
      "options": [
        {
          "value": "relevant_jobs",
          "description": "For each company this module returns a list of job postings based on the inputs."
        },
        {
          "value": "jobs_amount",
          "description": "The amount of job postings from the list of relevant jobs."
        }
      ]
    }
  }
}
```

#### Simple Example
```json
{
  "module_id": "hello_world",
  "lambda_name": "modules-helloworld_newstg_hello_world",
  "category": "enrich",
  "label": "Hello World",
  "description": "A simple module that greets the user",
  "api_key_required": false,
  "parameters": {
    "user_inputs": [
      {
        "id": "name",
        "label": "Name to greet",
        "component": "text_field",
        "optional": true,
        "help_text": "",
        "type": "text",
        "default_value": "World",
        "placeholder": "Enter a name"
      }
    ],
    "outputs": {
      "component": "checkbox_field_list",
      "options": [
        {
          "value": "greeting"
        },
        {
          "value": "message"
        }
      ]
    }
  }
}
```

### JSON Structure Details

- **Fields**:
  - `module_id`: Unique module identifier.
  - `lambda_name`: Name of the deployed Lambda function. **Important**: Use the format `modules-{team}_{stage}_{module_name}` (note the hyphen after "modules" and underscores elsewhere). Example: `modules-test_newstg_test-sum`
  - `category`: UI category (e.g., `enrich`, `ai`, `score`).
  - `label`: UI display name.
  - `description`: UI description.
  - `parameters`:
    - `enrichment_inputs`: Dynamic data inputs that flow through your module during execution. These represent the actual data being processed (e.g., company names, email addresses, IDs) that changes with each record in the pipeline. Think of them as actual inputs
    - `user_inputs`: Static configuration parameters that remain constant throughout the workflow execution. There are different UI input types, such as `dropdown`, `text_field`, `tags`, `multi_select_dropdown`, `code_editor`. Think of them as options for the module
    - `outputs`: Checkbox with output fields matching the module’s return dictionary.
- **Input/Output Mapping**:
  - `enrichment_inputs` and `user_inputs` IDs must match the `main` function’s input parameters.
  - `outputs` IDs must match the `main` function’s return dictionary keys.


### Registering on Scalestack

After your PR deployment succeeds (check the PR comment for confirmation):

1. **Navigate to the Staging Workbench**:
   ```
   https://staging.scalestack.ai/workbench
   ```

2. **Create and Register Your Module**:
   - Click "Create New Module"
   - Import your JSON configuration
   - The lambda_name should match what was deployed (check PR comments or AWS console)
   - Click "Publish" to complete registration

3. **If your module requires API keys** (`api_key_required: true`):
   - Register a service from the workbench first
   - Configure the API key in the service settings

4. **Test Your Module**:
   - Create a test workflow in the staging workbench
   - Verify your module appears in the appropriate category
   - Run a test execution to ensure it works correctly

5. **Production Deployment** (when ready):
   - After testing in staging, merge your PR to main
   - Follow your organization's process for production deployment
   - Register the module in production workbench: `https://platform.scalestack.ai/workbench`

## Repository Structure

The repository uses dynamic team detection:

```
third-party-modules/
├── .github/
│   ├── workflows/
│   │   └── deploy-staging-on-pr.yml    # Automated deployment pipeline
│   └── SECRETS_REQUIRED.md             # GitHub secrets documentation
├── modules_<teamname>/                 # Any team directory (auto-detected)
│   └── <module_name>/                  # Your module
│       ├── index.py                    # Module code (REQUIRED)
│       └── requirements.txt            # Auto-generated by GitHub Actions
├── cdk_dynamic_stacks.py               # Dynamic multi-stack CDK
├── cdk.json                            # CDK settings
├── pyproject.toml                      # Shared Python dependencies
├── poetry.lock                         # Dependency lock file
├── README.md                           # Quick start and team guide
└── DeveloperGuide.md                   # This guide (detailed development)
```

### Example with Multiple Teams:
```
third-party-modules/
├── modules_payments/                   # Payments team (auto-detected)
│   ├── stripe_integration/
│   └── paypal_processor/
├── modules_analytics/                  # Analytics team (auto-detected)
│   ├── user_metrics/
│   └── revenue_dashboard/
└── modules_ml/                         # ML team (auto-detected)
    ├── recommendation_engine/
    └── fraud_detector/
```

## Development Workflow Summary

1. **Clone repo and create feature branch** (use team name in branch)
2. **Create module in your team directory** (`modules_teamname/module_name/`)
3. **Write your module code** in `index.py`
4. **Test locally** with test.py
5. **Create PR to main** - your team's stack deploys automatically!
6. **Monitor deployment** via PR comments
7. **Register module** in staging workbench
8. **Test in staging** environment
9. **Merge PR** when ready for production

## Key Benefits of Dynamic Team Stacks

- **Zero configuration** - Just create `modules_<team>/` and go!
- **Team autonomy** - Each team owns their stack
- **No CDK edits** - Never touch CDK files
- **No conflicts** - Teams work in separate directories
- **Independent deployments** - Team stacks deploy in parallel
- **Clear ownership** - Easy to track which team owns what
- **Cost allocation** - AWS costs tracked per team stack
- **Infinitely scalable** - Add new teams without any configuration

This repository setup ensures consistent deployments, team isolation, and easy collaboration for third-party module development at scale - all without any CDK modifications!