[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/05/12 16:27:56.099637 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- FastAPI application skeleton with single `GET /` endpoint returning `{"message": "Hello World!"}`
- `src/optcg_api/` package structure with `app.py` and `__init__.py`
- Root `main.py` entry point importing `optcg_api.app:app`
- `opapi` CLI script alias mapped to `optcg_api.main:main`
- setuptools build system with packages discovered under `src/`
- `uv.lock` tracked in version control
- `CHANGELOG.md`, `CONTRIBUTING.md`, `CONTRIBUTORS`, and `README.md` License section
- Updated LICENSE to PBL v2.0
