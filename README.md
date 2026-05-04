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

Run these lightweight checks before pushing changes:

```bash
python3 -m py_compile campus_core/models/*.py campus_pmb/models/*.py campus_hr_academic/models/*.py campus_portal/controllers/*.py
python3 - <<'PY'
from pathlib import Path
from xml.etree import ElementTree as ET

for path in Path('.').glob('campus_*/**/*.xml'):
    ET.parse(path)
    print(f'OK {path}')
PY
```

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

## Recommended Next Steps

- Add a lint profile such as `pylint-odoo` or an agreed team linter.
- Review access rights with real campus roles before production use.
