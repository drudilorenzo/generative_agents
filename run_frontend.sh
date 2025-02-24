#!/bin/bash

FRONTEND_SCRIPT_PATH="environment/frontend_server"
FRONTEND_SCRIPT_FILE="manage.py"
CONDA_ENV="simulacra"
CONDA_PATH="/home/${USER}/anaconda3/bin/activate"

FILE_NAME="Bash-Script-Frontend"
echo "(${FILE_NAME}): Running frontend server"

# Parse conda-specific arguments first
while [[ $# -gt 0 ]]; do
    case "$1" in
        --conda_path)
            CONDA_PATH="${2}"
            shift 2
            ;;
        --env_name)
            CONDA_ENV="${2}"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

cd ${FRONTEND_SCRIPT_PATH}
source "${CONDA_PATH}" "${CONDA_ENV}" || {
    echo "Failed to activate conda environment. Please check your conda path and environment name."
    exit 1
}

PORT=8000
if [ -z "$1" ]
then
    echo "(${FILE_NAME}): No port provided. Using default port: ${PORT}"
else
    PORT=$1
fi

python3 ${FRONTEND_SCRIPT_FILE} runserver ${PORT}