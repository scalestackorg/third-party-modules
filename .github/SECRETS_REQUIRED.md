# GitHub Secrets Setup for Staging Deployment

To enable the automated deployment pipeline, you need to configure the following secrets in your GitHub repository.

## Required Secrets

Navigate to your repository's Settings → Secrets and variables → Actions, then add these secrets:

### 1. AWS Credentials
- **`AWS_ACCESS_KEY_ID`**: Your AWS Access Key ID
- **`AWS_SECRET_ACCESS_KEY`**: Your AWS Secret Access Key

### 2. Scalestack Artifact Registry Credentials
- **`POETRY_HTTP_BASIC_SCALESTACK_USERNAME`**: Your Scalestack username
- **`POETRY_HTTP_BASIC_SCALESTACK_PASSWORD`**: Your Scalestack password

## How to Add Secrets

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

## Where to Find Credentials

The actual credential values should be obtained from:
- **AWS Credentials**: From your AWS IAM console or your organization's AWS administrator
- **Scalestack Credentials**: From the DeveloperGuide.md or your Scalestack account administrator

⚠️ **IMPORTANT**: Never commit actual credentials to the repository. Always use GitHub Secrets for sensitive information.

## Workflow Triggers

The deployment workflow will automatically trigger when:
- A pull request is **opened** targeting the `main` branch
- New commits are **pushed** to an existing PR (synchronize)
- A closed PR is **reopened**

## Deployment Process

When a PR is created or updated:
1. The workflow checks out the code
2. Sets up Python 3.12 and Poetry
3. Installs dependencies including Scalestack SDK
4. Exports requirements for Lambda modules
5. Synthesizes the CDK stack
6. Deploys to AWS staging environment (`newstg`)
7. Comments on the PR with deployment status

## Testing Your Deployment

After successful deployment:
1. Check the PR comments for deployment confirmation
2. Access the [Staging Workbench](https://staging.scalestack.ai/workbench)
3. Test your modules in the staging environment
4. Register your modules if needed (see DeveloperGuide.md)

## Troubleshooting

If deployment fails:
- Check the workflow logs in the Actions tab
- Verify all secrets are correctly configured
- Ensure your module code follows the structure in DeveloperGuide.md
- Confirm your AWS credentials have the necessary permissions for CDK deployments