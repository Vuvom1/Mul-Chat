# NATS Credential Migration Guide

This guide explains how to migrate the NATS user credentials from the `NatsUserCredential` table to the `User` table.

## Overview

The migration process includes the following steps:

1. Update the model definitions to add NATS credential fields to the `User` table
2. Run a migration script to move data from the `NatsUserCredential` table to the `User` table
3. Update the application code to use the new structure
4. Drop the `NatsUserCredential` table

## Step 1: Update the Models

The following changes have been made to the model definitions:

1. Added NATS credential fields to the `User` model:
   - `nats_jwt`
   - `nats_seed_hash`
   - `nats_public_key`
   - `nats_account_id`
   - `nats_account_public_key`
   - `nats_expires_at`
   - `nats_expired_at`

2. Updated the `NatsAuthSession` model to remove the `credential_id` field and relationship to `NatsUserCredential`

3. Updated the `NatsAccount` model to remove the relationship to `NatsUserCredential`

## Step 2: Migrate the Data

Run the migration script to move data from the `NatsUserCredential` table to the `User` table:

```bash
cd /path/to/Mul-Chat
python scripts/migrate_nats_credentials.py
```

This script will:
1. Move all credential data from `NatsUserCredential` to the `User` table
2. Verify that all data has been migrated correctly
3. Update the `NatsAuthSession` table to remove the `credential_id` column

## Step 3: Update the Application Code

The following changes have been made to the application code:

1. Updated the `UserQueries` class to add methods for working with NATS credentials
2. Updated the `NatsAuthSessionQueries` class to remove the `credential_id` parameter
3. Updated the `auth_service.py` and `user_service.py` files to use the new structure

## Step 4: Drop the NatsUserCredential Table

After verifying that the application works correctly with the new structure, you can drop the `NatsUserCredential` table:

```bash
cd /path/to/Mul-Chat
python scripts/drop_nats_user_credential_table.py
```

## Troubleshooting

If you encounter any issues during the migration process, check the logs for error messages. You can run the migration script with the `--debug` flag to get more detailed logs:

```bash
python scripts/migrate_nats_credentials.py --debug
```

If the verification step fails, it means that some credentials may not have been migrated properly. You can try running the migration script again, or check the database manually to identify the problem.

## Rollback

If you need to roll back the migration, you can:

1. Restore the database from a backup
2. Revert the code changes
3. Recreate the `NatsUserCredential` table and relationships
