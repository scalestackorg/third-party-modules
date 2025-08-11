#!/usr/bin/env python3
"""
Fully dynamic CDK stack that automatically creates a separate stack for each team directory.
No CDK modifications needed - just create a modules_<teamname>/ directory and deploy!
"""

import os
import re
from pathlib import Path
from aws_cdk import App, CfnOutput, Stack, Tags
from constructs import Construct
from scalestack_architecture import PythonLambdaFactory

REGION = os.environ.get("AWS_REGION", "us-east-1")
STAGE = os.environ.get("STAGE", "newstg")

class SharedInfrastructureStack(Stack):
    """Shared resources that all teams can use."""
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        id = f"{id}-{STAGE}"
        super().__init__(scope, id, **kwargs)
        
        # Add any shared resources here (layers, VPC, etc.)
        # This stack deploys first and other stacks can reference it
        
        CfnOutput(self, "SharedResourcesDeployed", value="true")
        print("✅ Shared infrastructure stack configured")

class DynamicTeamStack(Stack):
    """Dynamically created stack for each team."""
    
    def __init__(self, scope: Construct, team_name: str, team_dir: Path, **kwargs) -> None:
        # Create unique stack ID for this team
        stack_id = f"Team{self._to_pascal_case(team_name)}Stack-{STAGE}"
        super().__init__(scope, stack_id, **kwargs)
        
        self.team_name = team_name
        self.team_dir = team_dir
        
        print(f"\n🏗️  Creating stack for team: {team_name}")
        
        # Create Lambda factory for this team
        self.lambda_factory = PythonLambdaFactory(
            stack=self,
            scope=scope,
            prefix=f"modules-{team_name}",
            stage=STAGE,
            python_version="3.12",
            # architecture="x86_64",
        )
        
        # Deploy all modules for this team
        modules_deployed = self._deploy_team_modules()
        
        # Output summary
        if modules_deployed:
            CfnOutput(self, "ModulesDeployed", value=", ".join(modules_deployed))
            print(f"✅ Team {team_name}: Deployed {len(modules_deployed)} modules")
        else:
            print(f"⚠️  Team {team_name}: No modules found in {team_dir}")
    
    def _deploy_team_modules(self):
        """Deploy all modules found in the team's directory."""
        modules_deployed = []
        
        # Find all module directories (containing index.py)
        for module_dir in self.team_dir.iterdir():
            if module_dir.is_dir() and (module_dir / "index.py").exists():
                module_name = module_dir.name
                print(f"  📦 Deploying module: {module_name}")
                
                # Deploy the Lambda function
                lambda_function = self.lambda_factory.new_function(
                    name=module_name,
                    handler="main",
                    index="index",
                    folder=str(module_dir.relative_to(Path.cwd())),
                )
                
                # Create CloudFormation output
                output_name = self._to_pascal_case(f"{self.team_name}_{module_name}")
                CfnOutput(self, output_name, value=lambda_function.function_name)
                
                modules_deployed.append(module_name)
        
        return modules_deployed
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(x.title() for x in snake_str.split('_'))

def discover_teams(repo_root: Path):
    """Discover all team directories (modules_* pattern)."""
    teams = []
    
    # Pattern to match team directories
    team_pattern = re.compile(r'^modules_([a-z][a-z0-9_]*)$')
    
    for item in repo_root.iterdir():
        if item.is_dir():
            match = team_pattern.match(item.name)
            if match:
                team_name = match.group(1)
                teams.append((team_name, item))
                print(f"🔍 Discovered team: {team_name} -> {item.name}/")
    
    return teams

# Create the CDK app
app = App()

# Get repository root
repo_root = Path(__file__).parent

# Deploy shared infrastructure first
print("=" * 60)
print("DYNAMIC MULTI-STACK DEPLOYMENT")
print("=" * 60)
shared_stack = SharedInfrastructureStack(app, "ScalestackShared")

# Discover and create stacks for all teams
teams = discover_teams(repo_root)

if not teams:
    print("\n⚠️  No team directories found!")
    print("Create a directory named 'modules_<teamname>/' to get started.")
    print("Example: modules_alpha/, modules_payments/, modules_data/")
else:
    print(f"\n📊 Found {len(teams)} team(s) to deploy")
    
    # Create a stack for each team
    team_stacks = []
    for team_name, team_dir in teams:
        team_stack = DynamicTeamStack(app, team_name, team_dir)
        team_stack.add_dependency(shared_stack)
        
        # Add tags for the team
        Tags.of(team_stack).add("team", team_name)
        Tags.of(team_stack).add("stage", STAGE)
        Tags.of(team_stack).add("project", "dynamic-modules")
        
        team_stacks.append(team_stack)

# Add global tags to shared stack
Tags.of(shared_stack).add("stage", STAGE)
Tags.of(shared_stack).add("project", "dynamic-modules")
Tags.of(shared_stack).add("type", "shared-infrastructure")

print("\n" + "=" * 60)
print("CDK synthesis complete!")
print("=" * 60)

app.synth()