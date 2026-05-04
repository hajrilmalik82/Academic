# Campus Management Odoo Addons

This repository contains Odoo 17 addons for a university ERP workflow.

## Modules

- `campus_core`: core academic models for facilities, institutions, subjects,
  KRS, KHS, classes, schedules, sessions, and student profiles.
- `campus_pmb`: admissions workflow and portal account creation for accepted
  applicants.
- `campus_hr_academic`: academic profile fields for lecturers on `hr.employee`.
- `campus_portal`: student portal pages for viewing KRS and KHS records.

## Requirements

- Odoo 17
- Python dependencies provided by the Odoo runtime, including `pytz`

Install these addons by adding the repository path to the Odoo addons path,
updating the app list, and installing the required modules from Apps.

## Quality Checks

Run the local validation script before pushing changes:

```bash
python3 tools/validate_addons.py
```

GitHub Actions runs the same validation automatically on pushes and pull
requests to `main`. If `ruff` is available, the workflow also runs the
configured Python lint checks from `pyproject.toml`.

Run the Odoo transaction tests from an Odoo 17 environment with the addons path
configured, for example:

```bash
odoo-bin -d test_db --test-enable --stop-after-init -i campus_core
```

## Business Rules Covered

- KRS records are unique per student, academic year, and term.
- KRS lines cannot repeat the same subject in one KRS.
- KRS can only be approved after submission.
- KHS records are unique per student, academic year, and term.
- KHS grades must be between 0 and 100.
- Room capacity must be greater than zero.
- Class schedules validate time ranges and prevent room or lecturer overlaps.
- Admissions accounts can only be created after an applicant passes.

## Access Model

- Campus administrators manage academic master data, KRS, KHS, schedules, and
  classes.
- Lecturers have read-only access to academic reference data, KRS, KHS, and KHS
  lines by default.
- Portal students can read only their own KRS and KHS records through record
  rules. Direct portal create/write access is disabled at the ACL level; any
  future self-service editing should be implemented through explicit portal
  controllers that enforce state and ownership checks.

## Suggested Contribution Flow

1. Create a branch from the latest `main`.
2. Make focused changes.
3. Run `python3 tools/validate_addons.py`.
4. Run Odoo tests in an Odoo 17 database when changing business logic.
5. Open a pull request to `main` and wait for GitHub Actions to pass.

## Recommended Next Steps

- Add `pylint-odoo` in an Odoo-capable CI image for deeper Odoo-specific linting.
- Add module installation tests for `campus_pmb`, `campus_hr_academic`, and
  `campus_portal`.
- Review access rights with real campus roles before production use.
