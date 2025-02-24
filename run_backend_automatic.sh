#!/bin/bash

BACKEND_SCRIPT_PATH="reverie/backend_server"
BACKEND_SCRIPT_FILE="automatic_execution.py"
CONDA_ENV="simulacra"
CONDA_PATH="/home/${USER}/anaconda3/bin/activate"
LOGS_PATH="../../logs"

FILE_NAME="Bash-Script"
cd ${BACKEND_SCRIPT_PATH}

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

source "${CONDA_PATH}" "${CONDA_ENV}" || {
    echo "Failed to activate conda environment. Please check your conda path and environment name."
    exit 1
}

ARGS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --origin|-o)
            ARGS="${ARGS} --origin ${2}"
            shift 2
            ;;
        --target|-t)
            ARGS="${ARGS} --target ${2}"
            TARGET=${2}
            shift 2
            ;;
        --steps|-s)
            ARGS="${ARGS} --steps ${2}"
            shift 2
            ;;
        --ui)
            ARGS="${ARGS} --ui ${2}"
            shift 2
            ;;
        --browser_path|-bp)
            ARGS="${ARGS} --browser_path ${2}"
            shift 2
            ;;
        --port|-p)
            ARGS="${ARGS} --port ${2}"
            echo "(${FILE_NAME}): Running backend server at: http://127.0.0.1:${2}/simulator_home"
            shift 2
            ;;
        --load_history|-h)
            ARGS="${ARGS} --load_history ${2}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters
echo "(${FILE_NAME}): Arguments: ${ARGS}"

timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
echo "(${FILE_NAME}): Timestamp: ${timestamp}"
mkdir -p ${LOGS_PATH}
python3 ${BACKEND_SCRIPT_FILE} ${ARGS} 2>&1 | tee ${LOGS_PATH}/${TARGET}_${timestamp}.txt