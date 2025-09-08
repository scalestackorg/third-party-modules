# Developer Guide for Third-Party Module Integration

[![GitHub](https://img.shields.io/badge/GitHub-third--party--modules-181717?logo=github)](https://github.com/scalestackorg/third-party-modules)

This guide provides detailed steps for developing, deploying, and registering modules on the Scalestack platform using this repository's automated CI/CD pipeline.

**🚀 Start Building Now:** Open this repo in Claude Code or Cursor → Ask the AI to create your module → It will follow this guide automatically!

## Overview

This repository is configured with GitHub Actions to automatically deploy your modules to staging when you create a pull request to the main branch. The deployment process is streamlined:

1. **Clone repo and create feature branch** (use team name in branch)
2. **Create module in your team directory** (`teamname/your_module_name/`)
3. **Write your module code** in `index.py`
4. **Test locally** with test.py
5. **Create PR to main** - your team's stack deploys automatically!
6. **Monitor deployment** via PR comments
7. **Register module** in staging workbench
8. **Test in staging** environment
9. **Wait for approval and merge PR** when ready for production

The platform uses an Orchestrator Service with Amazon SQS to queue module execution commands, dispatched via Amazon SNS to individual module queues. The `scalestack_sdk` library simplifies input/output handling for modules.

## Quick Start

### Prerequisites
1. Clone this repository and **Create a new branch**:
```bash
git clone https://github.com/scalestackorg/third-party-modules
cd third-party-modules
git checkout -b feature/team-name/module-name
```

2. Ensure Poetry is installed and the project is initialized:
```bash
export POETRY_HTTP_BASIC_SCALESTACK_USERNAME="buplex"
export POETRY_HTTP_BASIC_SCALESTACK_PASSWORD="jrh-bxq0aur6HDB8vjn"
```

```bash
    poetry env use python3.12
    poetry install
    poetry shell
```

## 1. Developing a Module in This Repository

### Dynamic Team Structure

This repository uses a **fully dynamic team-based organization**. Simply create a directory with the pattern `modules_<teamname>/` and the CDK automatically creates a stack for your team! (`<teamname>` can be your company name)

```
third-party-modules/
└── modules_<teamname>/  # Your team's directory (auto-detected)
    └── your_module_name/     # Your module
        └── index.py     # Module code
```

### Creating Your Module

1. **Create your team directory** (if it doesn't exist):
```bash
# Choose a team name and create the directory
mkdir modules_<teamname>/
```

2. **Create your module within your team's directory**:
```bash
mkdir modules_<teamname>/your_module_name
touch modules_<teamname>/your_module_name/index.py
```

3. The `scalestack_sdk` library is pre-installed in the shared Poetry environment

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

@decorators.aws
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
- If the module needs an API key, add `api_key` as a parameter
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

- **Add to the main Poetry project**:
```bash
poetry add <package-name>
```

Note: The `requirements.txt` file is auto-generated during deployment - you don't need to create it manually.

### Example of complex module (index.py)

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

## 2. Deploying Your Module

Deployment to staging happens automatically through GitHub Actions when you create a pull request to the main branch.

### Deployment Steps

1. **Commit your module** to your feature branch:
```bash
git add modules_<teamname>/your_module_name/
git commit -m "[<teamname>] Add new module: your_module_name"
git push origin feature/<teamname>/your_module_name
```

2. **Create a Pull Request** to the main branch on GitHub.

### Automated Deployment Process

When you create or update a PR:

1. **GitHub Actions automatically:**
  - Sets up the Python environment
  - Installs all dependencies
  - Exports requirements.txt for each module
  - Runs CDK synth to validate the stack
  - Deploys to AWS staging environment (`newstg`)

2. **Monitor deployment:**
  - Check the Actions tab in GitHub for progress
  - Review the PR comment for deployment confirmation
  - If deployment fails, check the logs for errors

> **⚠️ Important:** Every time you push a new commit to your open PR, the module will automatically re-deploy to staging. This enables rapid iteration and testing. The deployment status will be updated in the PR comments after each push.

## 3. Registering Your Deployed Module

After your module is successfully deployed to staging via the GitHub Actions pipeline, register it for frontend integration.

**💡 Tip:** We strongly recommend to ask Claude Code to create the registration JSON and save it in a .json file

### JSON Structure

Create a JSON file to define the module’s UI components and backend integration.

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

#### Example (Job Posting Module)
```python
{
  "module_id": "job_posting_enrichment",
  "lambda_name": "modules-jobposting_newstg_job_posting", # Format: modules-{teamname}_{stage}_{your_module_name}
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


### Registering on Scalestack

After your PR deployment succeeds (check the PR comment for confirmation):

1. **Navigate to the Staging Workbench**:
  ```
  https://staging.scalestack.ai/workbench
  ```

2. **Create and Register Your Module**:
  - Select "Create New Module"
  - Import your JSON configuration ('JSON' button on the top left corner)
  - The lambda_name should match what was deployed (check PR comments or AWS console)
  - Click "Publish" to complete registration

3. **If your module requires API keys** (`api_key_required: true`):
  
  **Option 1: Using an existing service**
  - Check if the service for your API key already exists in Settings -> Integrations
  - Common services like OpenAI, Apollo, Anthropic, etc. may already be configured
  - If the service exists, simply register your API key there
  
  **Option 2: Using Third Party Modules service**
  - If the service for your API key doesn't exist, use the **"Third Party Modules"** service
  - On the workbench, click on "Register Service" and select **"Third Party Modules"**
  - Register your API key in the Settings -> Integrations tab under "Third Party Modules"
  - Configure the API key value in the service settings
  
  > **Note:** The "Third Party Modules" service acts as a general-purpose container for API keys that don't have their own dedicated service yet

4. **Test Your Module**:
  - Create a test workflow in the staging workbench
  - Run a test execution to ensure it works correctly

5. **Production Deployment** (when ready):
  - After testing in staging, wait for approval and Scalestack's team will merge your PR to main
  - Register the module in production workbench: `https://platform.scalestack.ai/workbench`

## Repository Structure

The repository uses dynamic team detection:

```
third-party-modules/
├── .github/
│   ├── workflows/
│       └── deploy-staging-on-pr.yml    # Automated deployment pipeline
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