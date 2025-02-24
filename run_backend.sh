#!/bin/bash

BACKEND_SCRIPT_PATH="reverie/backend_server"
BACKEND_SCRIPT_FILE="reverie.py"
CONDA_ENV="simulacra"
CONDA_PATH="/home/${USER}/anaconda3/bin/activate"
LOGS_PATH="../../logs"

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

cd ${BACKEND_SCRIPT_PATH}
source "${CONDA_PATH}" "${CONDA_ENV}" || {
    echo "Failed to activate conda environment. Please check your conda path and environment name."
    exit 1
}

echo "Running backend server at: http://127.0.0.1:8000/simulator_home"
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
echo "Timestamp: ${timestamp}"
mkdir -p ${LOGS_PATH}
python3 ${BACKEND_SCRIPT_FILE} --origin ${1} --target ${2} 2>&1 | tee ${LOGS_PATH}/${2}_${timestamp}.txt