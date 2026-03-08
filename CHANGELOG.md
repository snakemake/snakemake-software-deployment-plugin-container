# Changelog

## [0.5.0](https://github.com/snakemake/snakemake-software-deployment-plugin-container/compare/v0.4.0...v0.5.0) (2026-03-08)


### Features

* add apptainer support (plus various small fixes) ([#11](https://github.com/snakemake/snakemake-software-deployment-plugin-container/issues/11)) ([54a5c70](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/54a5c70a6ca1ca9ff9b39cd16dc6a7d86ebd2df7))

## [0.4.0](https://github.com/snakemake/snakemake-software-deployment-plugin-container/compare/v0.3.0...v0.4.0) (2026-02-27)


### Features

* implement check whether given executable is contained in container image ([9edf4a6](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/9edf4a6d4a80cea414bdbc844a58d052e2e8db0a))


### Bug Fixes

* adapt to latest changes in interface ([3c5fd0b](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/3c5fd0bda99ec3e64dbe0b2b9012e14287759509))

## [0.3.0](https://github.com/snakemake/snakemake-software-deployment-plugin-container/compare/v0.2.1...v0.3.0) (2026-02-18)


### Features

* always mount system tempdir ([60ef0bd](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/60ef0bd3384edffc8816b687b88a321da4b053f3))

## [0.2.1](https://github.com/snakemake/snakemake-software-deployment-plugin-container/compare/v0.2.0...v0.2.1) (2026-02-17)


### Bug Fixes

* fix mountpoint handling ([#7](https://github.com/snakemake/snakemake-software-deployment-plugin-container/issues/7)) ([ce2c1c9](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/ce2c1c9cd29820835468ac4b8c808a4b6e114ee9))

## [0.2.0](https://github.com/snakemake/snakemake-software-deployment-plugin-container/compare/v0.1.0...v0.2.0) (2026-02-17)


### Features

* additional mountpoints ([#5](https://github.com/snakemake/snakemake-software-deployment-plugin-container/issues/5)) ([29ba897](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/29ba897154bac2082d42048c601a6177e0db0d82))

## 0.1.0 (2026-02-13)


### Bug Fixes

* do not mount a folder that does not exist ([1e78c0b](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/1e78c0bb0ff3c4066c99b6a0cdb29873f1094e76))
* mount cache folder inside container ([9a2ff7b](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/9a2ff7b4f95cb491a84f11d722381c0de7d810cd))
* typing and class naming, migrate to pixi ([6be2502](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/6be25021166cc610eeb74f4c8a0b6c9b09052a58))
* use ContainerType enum ([b2964fe](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/b2964fe5b224a3dd1e917d7f31a5dca51fe0fb0b))
* use shlex for more robust shell escaping ([1f650db](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/1f650db150bb4d80a7ab73c65ff0a9fdfd4820f4))
* use shlex for more robust shell escaping ([ea77d4a](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/ea77d4a637cc2057d606d63d743fac3b7aa925b5))


### Dependencies

* bump deps to latest stable snakemake release ([a4f3187](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/a4f3187a0a5d66c4d26013c3bbb7e707e8def674))


### Documentation

* add comment about tag in container URI ([e777fd7](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/e777fd78a7ba55386276ad3dce91b94fa8879f56))
* add TODO in README ([6d461e5](https://github.com/snakemake/snakemake-software-deployment-plugin-container/commit/6d461e5d94ecb20e98d13460e93bd6fa2b6b4a88))
