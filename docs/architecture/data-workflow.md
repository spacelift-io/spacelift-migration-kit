# Data Workflow

## Overview

The whole goal of SMK is to replicate the setup the user has at their current vendor in Spacelift as closely as possible. Each solution is different so there mapping is never perfect and trade-offs have to be made sometimes. Also, beyond their current vendor setup, each user will have other constraints (time, experience, dependencies on other teams, imposed timeline or time-window to migrate, dependencies between entities to migrate that requires a specific order, etc.) so there is no one-size-fits-all solution. As a result, while SMK should provide a migration workflow that works for most users, it must remain flexible and extensible to accommodate the unavoidable edge cases.

### Workspace Structure

SMK uses a "migration folder" that contains everything related to the migration. The user configures it as their first action after installing SMK, possibly with the `init` command. This creates a folder (default: ~/.smk, customizable via an option).

The folder contains:

- **config.yaml**: Configuration file
- **data/source**: Raw or minimally processed data from the source vendor
- **data/transformed**: Structured Spacelift entities data extracted from the source data, transformed, and mapped
- **data/generated**: HCL code to create the Spacelift entities. Used as a git clone for the git repository that holds this code so that entities can be created by the administrative stack
- **logs/**: Structured migration logs

Generally, we want to keep detailed track of every action for auditability.

### Resumability

Each stage should try to resume gracefully whenever practical. We might need to keep a Write-Ahead Log (WAL) to accurately determine where a stage stopped and continue safely, because data integrity is paramount.

If export fails partway through (e.g., 500 of 1000 stacks), it should ideally resume from where it stopped. WAL could allow us to determine where the stage stopped and resume gracefully.

### State Tracking

SMK uses a local SQLite database to keep track of existing and migrated entities. This allows us to easily keep a reliable track of what has been done and what remains, including what has been ignored and possibly why. Adding SQLite as a dependency is reasonable here.

### Stage Skipping

Every stage can be skipped provided the user creates the output that is suitable for the next stage. This is likely too much work for little benefit but to handle edge-cases, the user might want to tweak the stage code via a plugin to override some behavior (preferred) or manually tweak the output. Manual tweaks are discouraged because they would be overwritten should they need to run the stage again.

### Batching

Most migrations must be broken down in batches for various reasons (e.g., number of entities to migrate, dependencies between entities, need for a test drive, inability to migrate some entities yet for business reasons).

Users create a batch by selecting a subset of entities and getting them through the whole process together. Then create another batch and repeat. This allows us to track progress. Each batch goes through all stages before the next batch begins.

Migrating all entities at once is a special case where all the entities are selected in a single batch.

## Workflow Stages

### 1. Export

The export stage is foundational because its purpose is to export as much information as possible about the setup at the current vendor so that we can work off of this material and build the closest Spacelift setup we can.

#### Data Sources

This stage only pulls data from the source vendor. It should only modify the source setup when absolutely needed to export data. This should be temporary and reversed once the data has been exported. The user must be provided clear information about the reason for this, what is being done, and get their approval. Without explicit user approval, nothing should be changed in the source setup.

This stage also provides a way to read raw data in a structured way, regardless of the nature of the data stored (i.e., data is parsed and returned as Pydantic models).

#### Data Collection

Everything related to the setup of the deployment pipelines and supporting entities is collected. The user should be able to filter out some entities at that stage but it is discouraged as it can lead to issues down the road. It should be used only to ignore entities that should not be migrated to Spacelift ever (e.g., deprecated/unused entities, broken entities that are not worth fixing). Ignoring entities this early is tricky because entities that need to be migrated might share dependencies with filtered out entities. Filtering out those shared dependencies would result in issues at a later stage.

Data is pulled from the current vendor in the appropriate way for that vendor. This is typically done through an API but it could also require collecting configuration files or source code.

#### Storage

Raw data is stored in the `data/source` directory. The data is minimally processed, if at all, and stored. It should never be edited via SMK or manually as it is the source of truth for all subsequent processing. For APIs, store the responses as-is whenever practical. For configuration and source code, store a copy of the files locally.

#### Error Handling

SMK ensures the completeness (taking filters into account) and integrity of the data. Data retrieval should be retried until successful with back-off strategies and obeying rate limits. If data cannot be successfully retrieved, let the user know and suggest next steps.

The process must allow for entities to be migrated multiple times safely because the source setup might change. This is discouraged because it could lead to unexpected side-effects but we should try our best to handle it safely because that is the reality users live in.

#### Validation

- Keep a hash of each file so that modification can be spotted easily in case we need to troubleshoot issues
- Data is validated with Pydantic models to spot integrity issues, unexpected changes in the data format, or possible issues that could complicate the migration and need to be discussed upfront to determine the best course of action (e.g., feature that does not map to any Spacelift feature and requires a workaround)
- Add a header to the stored file when format permits to warn the user

### 2. Transform

At this stage, the raw data is transformed and mapped to Spacelift entity types.

#### Processing

Transformation includes adding, editing, and ignoring data. This happens independently from the raw data that is never modified in any way. Mapping might require merging or splitting source entities to map to Spacelift ones.

Transformed data is stored in the `data/transformed` directory.

#### User Overrides

Users can edit or override transformations via a plugin that registers to specific hooks to override core processing and plugin processing. This allows even plugin behaviors to be tweaked by the user to their liking.

#### Dry-Run

Stages should provide a dry run option whenever practical. The default behavior should be that the user needs to interactively confirm they want to proceed or use the `--force` option to proceed without performing a dry-run.

#### Data Structures

Input is the raw data. Output is lists of Spacelift entities described as Pydantic models.

#### Validation

Pydantic models have validation rules to ensure data integrity. This catches issues caused by the Transform stage.

### 3. Generate

Creates the HCL code that describes the resources needed to replicate the source vendor setup in Spacelift via the Spacelift provider.

#### Output

HCL code, compatible with both Terraform and OpenTofu. OpenTofu is the default option.

Generated code is stored in the `data/generated` folder in the SMK migration folder. It should be organized in a few files. There must be the recommended files (e.g., providers.tf) and we should probably split the entities in a few files for ease of maintainability but the best layout is still to be determined. Options include grouping by Spacelift entity type, space, or specific labels.

SMK can provide a handful of templates for common layouts and leave users the ability to create their own template.

#### Manual Edits

SMK keeps track of a checksum to spot modified HCL files to help with troubleshooting. It is acceptable for users to modify generated HCL to handle edge cases SMK cannot handle.

If a user manually edits generated HCL and then re-runs the generate stage, SMK detects modified files using the checksum, asks the user what to do, and if the user chooses to overwrite, git will show them a diff of the changes so they can handle conflicts there.

#### Data Structures

Input: Structured data that describes the Spacelift entities to be created.
Output: Formatted and valid HCL code.

#### Validation

Generated code is formatted and validated.

### 4. Publish HCL Code

The generated, and possibly hand-edited, HCL code needs to be stored in a git repository to be used by an administrative stack. This stage is about committing and pushing code to that repository.

**Note**: Administrative stacks are deprecated. Research the new recommended setup. (TODO: Research task)

This needs to be an iterative process because users will most likely migrate in batches.

#### Implementation

For v3, this is a guidance-only stage. SMK provides guidance and lets the user achieve it the way they see fit. The git workflow (branch strategy, PR-based or direct commits) is left to the user. Git credentials are out of scope and for the user to figure out.

This approach could be revisited later to add automation.

#### Multi-Batch Support

The generated Terraform code layout should allow for later migration of new entities. The specific HCL layout to support multiple batches needs experimentation (separate files per batch? per entity?). (TODO: Research task)

How to handle re-migration of already migrated entities is an edge case to document and leave out for now.

#### Validation

The git commit and push must succeed.

### 5. Apply

This stage is about triggering a tracked run on the administrative stack to create the Spacelift entities.

#### Execution

The user manually triggers the run or SMK does it via the API. Then, SMK could open the browser to the run page or display progress in the terminal.

#### Partial Apply

Users could do partial applies via [Spacelift's targeted replan feature](https://docs.spacelift.io/concepts/run/tracked#targeted-replan) but this should be kept for edge cases as all entities for a batch should be created together in most cases.

#### Error Handling

Terraform/OpenTofu does not roll back so the user would have to figure out what happened and fix it. It could be something unrelated to the migration that conflicts with it or some bogus HCL code was generated. In that latter case, they would need to fix the process or the generated code and re-apply.

#### Tracking

SMK tracks what's been applied vs pending via Spacelift's API to confirm the migration has been fully completed.

#### Validation

The tracked run must succeed.

### 6. Post-Apply Actions

Migrating from some vendors requires performing additional actions after creating the Spacelift entities and before using them. For example:

- Terraform stacks might need their state file migrated to Spacelift before they can run
- Terraform/OpenTofu modules might need their versions created at Spacelift
- Terraform source code might need updates to point to the Spacelift module registry or remove the state backend configuration block for the source vendor

These actions depend on the source vendor and are provided by the plugin for the source vendor.

#### Guidance Display

Plugins that integrate with a source vendor register instructions that SMK displays to the user to provide them with guidance along the way, even if SMK does not provide the specific actions. This is part of the action registration.

Instructions are proactively displayed in the command outputs when using the CLI. When using the TUI, SMK displays a progress bar at all times (like a status bar) and provides dedicated screens where users can get more details about progress. Additionally, in the TUI, guidance is displayed on screen.

#### Automation

Like all other actions, these should be automated if they can be. Otherwise, SMK should provide the best guidance it can to help the user perform and verify the action.

### 7. Testing

At this stage, the user must thoroughly test the migrated entities to confirm functionality. They will likely need to engage other users and teams to confirm things look good. Do not rush this stage because there are many nuances to migrations. While the main use case might be working there might be edge cases that need adjustment.

This stage is primarily user guidance with optional API verification. SMK might be able to verify a few things via the API such as existence of the entities and possibly comparing their setup with the definition, but it might be overkill because it would effectively test the Spacelift provider's behavior which is out of scope.

### 8. Cleanup

Once everything has been confirmed to have been migrated and be working, the user can clean up their setup at their previous vendor. Depending on the vendor it might mean different things. The plugins should provide guidance, especially around things that could conflict with Spacelift.

SMK should not modify the source setup so it should not perform any cleanup actions, but it could provide guidance via the plugin for the source vendor.

## Data Structures

### Export Stage Models

The models for the Export stage depend on the source vendor. Their purpose is to immediately spot a change in format so that we do not silently mishandle data because the source format changed unexpectedly. Data integrity is paramount so we want data validation at every step of the way and stop immediately if something is off.

### Spacelift Entity Models

The models for Spacelift entities are fixed and meant to ensure that the data has been properly transformed and is compatible with the Spacelift provider.

### Model Evolution

The data is moved from the Export stage models to the Spacelift entity models by the Transform stage code.

## Plugin Responsibilities

### Core vs Plugins

Generally, the core provides the foundational capabilities and overall workflow management.

Depending on the stage, the core might orchestrate actions from the plugins to avoid duplicating behavior between different plugins (e.g., data transformation where the logic is shared but the plugins provide the transformers) or might fully delegate the stage to the plugin (e.g., post-apply actions).

### Plugin Registration

Plugins register for plugin hooks. Multiple plugins can register for the same hook. Depending on the hook, the core can decide to either call the last registered plugin (e.g., custom plugin created by the user to tweak some behavior) or call the plugin enabled in the configuration for a specific type (e.g., the VCS provider plugin to list module tags). There are no current use cases for calling all registered plugins for a hook.

### Hook Specifications

Hook specifications for each workflow stage are to be determined at a later time.

## Edge Cases

Edge cases will be documented as they are discovered during implementation.

## Error Handling

SMK is available as a CLI/TUI application. It follows all the best practices for these types of applications, including proper exit codes, log files, and meaningful messages to the user.

### Severity Levels

Generally, to ensure data integrity, SMK should be paranoid and stop if anything feels off but not all errors need to be fatal. There might be recoverable warnings. Those need to clearly explain what happened and what was done to recover so that it was safe to continue.

### Recovery

Recovery mechanisms depend on the stage. See the Resumability section for details on how stages can resume gracefully after failures.

## Action Tracking

Keep track of every action performed in structured log files so that we can troubleshoot issues and audit the user's behavior to improve the tool. The logs are stored locally and are shared with Spacelift voluntarily. There is no data exfiltration mechanism. All data sharing must be explicitly approved by the user.

### Log Format

Logs use JSON Lines format, managed by a Python logging library such as Structlog.

### Log Detail

Logs contain enough detail for users to troubleshoot issues on their own if they have the skills and will to do so, and for Spacelift to provide support.

### Sharing

The logs live on the user's machine. They would need to manually send them to Spacelift. They can review and redact them as they see fit.
