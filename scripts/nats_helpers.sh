#!/bin/bash
# NATS Helper Functions
# Source this file to get helper functions for namespaced NATS operations
#
# Usage:
#   source scripts/nats_helpers.sh
#   nats_stream_name "error_reports"  # Returns: ABSTRACT_AGENT_TEAM_ERROR_REPORTS
#   nats_subject "errors.staging"     # Returns: abstract_agent_team.errors.staging

# Load environment
if [ -f .env ]; then
    source .env
fi

# Ensure namespace is set
if [ -z "$NATS_NAMESPACE" ]; then
    echo "Error: NATS_NAMESPACE not set. Set it in .env file." >&2
    return 1
fi

# Generate namespaced stream name (UPPERCASE)
nats_stream_name() {
    local stream_suffix="$1"
    echo "${NATS_NAMESPACE^^}_${stream_suffix^^}"
}

# Generate namespaced subject (lowercase)
nats_subject() {
    local subject_suffix="$1"
    echo "${NATS_NAMESPACE,,}.${subject_suffix,,}"
}

# Create a namespaced stream
nats_create_stream() {
    local stream_suffix="$1"
    local subject_suffix="$2"
    local retention="${3:-workqueue}"  # workqueue or limits

    local stream=$(nats_stream_name "$stream_suffix")
    local subject=$(nats_subject "$subject_suffix")

    echo "Creating stream: $stream"
    echo "Subject pattern: $subject"

    ~/bin/nats stream add "$stream" \
        --subjects="$subject" \
        --retention="$retention" \
        --context=gcp-orchestrator
}

# List all streams for this project
nats_list_project_streams() {
    echo "Streams for project: $NATS_NAMESPACE"
    ~/bin/nats stream list --context=gcp-orchestrator | grep -i "^${NATS_NAMESPACE^^}_"
}

# Subscribe to a namespaced subject
nats_subscribe() {
    local subject_suffix="$1"
    local subject=$(nats_subject "$subject_suffix")

    echo "Subscribing to: $subject"
    ~/bin/nats sub "$subject" --context=gcp-orchestrator
}

# Publish to a namespaced subject
nats_publish() {
    local subject_suffix="$1"
    local message="$2"
    local subject=$(nats_subject "$subject_suffix")

    echo "Publishing to: $subject"
    ~/bin/nats pub "$subject" "$message" --context=gcp-orchestrator
}

# Get stream info for this project
nats_stream_info() {
    local stream_suffix="$1"
    local stream=$(nats_stream_name "$stream_suffix")

    ~/bin/nats stream info "$stream" --context=gcp-orchestrator
}

# Export functions for use in subshells
export -f nats_stream_name
export -f nats_subject
export -f nats_create_stream
export -f nats_list_project_streams
export -f nats_subscribe
export -f nats_publish
export -f nats_stream_info

echo "NATS helpers loaded for project: $NATS_NAMESPACE"
echo ""
echo "Available functions:"
echo "  nats_stream_name <suffix>        - Generate namespaced stream name"
echo "  nats_subject <suffix>            - Generate namespaced subject"
echo "  nats_create_stream <stream> <subject> [retention]"
echo "  nats_list_project_streams        - List all streams for this project"
echo "  nats_subscribe <subject>         - Subscribe to namespaced subject"
echo "  nats_publish <subject> <msg>     - Publish to namespaced subject"
echo "  nats_stream_info <stream>        - Get stream info"
echo ""
echo "Examples:"
echo "  nats_stream_name 'error_reports'              # -> ${NATS_NAMESPACE^^}_ERROR_REPORTS"
echo "  nats_subject 'errors.staging'                 # -> ${NATS_NAMESPACE,,}.errors.staging"
echo "  nats_create_stream 'tasks' 'tasks.>' 'workqueue'"
echo "  nats_subscribe 'errors.>'"
echo "  nats_publish 'tasks.test' '{\"test\": true}'"
