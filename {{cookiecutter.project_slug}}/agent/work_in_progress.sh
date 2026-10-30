work_in_progress() {
    local worktree="$1" base="$2"
    [[ -n "$(git -C "${worktree}" status --porcelain -- . ':(exclude)agent')" ]] && return 0
    git -C "${worktree}" diff --quiet "${base}" HEAD -- . ':(exclude)agent' && return 1
    [[ "$(cat "${worktree}/agent/.verified" 2>/dev/null)" != "$(git -C "${worktree}" rev-parse HEAD)" ]]
}
