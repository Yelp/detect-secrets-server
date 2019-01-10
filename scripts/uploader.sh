#!/bin/bash
# This script pretty much just follows the instructions from
# https://packaging.python.org/tutorials/packaging-projects/
# and uploads this package to pypi.

function usage() {
    echo "Usage: uploader.sh [test|public]"
    echo "Specify the pypi instance you want to upload to."
    echo "  - test:   uploads to test.pypi.org"
    echo "  - public: uploads to pypi.org"
}

function main() {
    local mode="$1"
    if [[ -z "$mode" ]]; then
        usage
        return 0
    fi
    if [[ "$mode" != "public" ]] && [[ "$mode" != "test" ]]; then
        usage
        return 1
    fi

    # Install dependencies
    pip install setuptools wheel twine

    # Create distribution files
    python setup.py sdist bdist_wheel

    uploadToPyPI "$mode"
    testUpload "$mode"
    if [[ $? == 0 ]]; then
        echo "Success!"
        rm -r build/ dist/
    fi
}

function uploadToPyPI() {
    # Usage: uploadToPyPI <mode>
    local mode="$1"
    if [[ "$mode" == "public" ]]; then
        twine upload dist/*
    else
        twine upload --repository-url https://test.pypi.org/legacy/ dist/*
    fi
}

function testUpload() {
    # Usage: testUpload <mode>
    local mode="$1"

    installFromPyPI "$mode"

    detect-secrets-server --version
    if [[ $? != 0 ]]; then
        echo "Failed installation!"
        return 1
    fi
}

function installFromPyPI() {
    # Usage: installFromPyPI <mode>
    local mode="$1"
    if [[ "$mode" == "public" ]]; then
        pip install detect-secrets-server
    else
        pip install --index-url https://test.pypi.org/simple/ detect-secrets-server
    fi
}


main "$@"
