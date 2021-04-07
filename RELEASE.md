# Release documentation

## Release process

In case the jupyter labextions and/or the python code has been changed:

1. Run tests

    ```bash
    make tests
    ```

2. Clean environment

    ```bash
    make clean    # delete all temp files
    make prepare  # commit deletions
    ```

3. Bump version of jupyter_cadquery

    - A new release candidate with rc0

      ```bash
      make bump part=major|minor|patch
      ```

    - A new build

      ```bash
      make bump part=build
      ```

    - A new release

      ```bash
      make bump part=release
      ```

    - A new release without release candidate

      ```bash
      make bump part=major|minor|patch version=major.minor.patch
      ```

4. Create distribution

    ```bash
    make dist
    ```

5. Create and tag release

    ```bash
    make release
    ```

6. Deploy to pypi

    ```bash
    make upload
    ```

7. Create Docker container

    ```bash
    make docker
    ```

7. Upload Docker container

    ```bash
    make upload_docker
    ```

### 3 Push changes

1. Push repo and tag

    ```bash
    git push
    git push origin --tags
    ```
