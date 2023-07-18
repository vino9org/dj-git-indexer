STATS_SQL = [
    """
    update commits
    set n_lines_changed = (
        select COALESCE(sum(n_lines_changed),0)
        from committed_files
        where committed_files.commit_id = commits.sha
        and is_superfluous is false
        )
    where true
    """,
    """
    update commits
    set n_files_changed = (
        select count(1)
        from committed_files
        where committed_files.commit_id = commits.sha
        and is_superfluous is false
    )
    where true
    """,
    """
    update commits
    set n_lines_ignored = (
        select COALESCE(sum(n_lines_changed),0)
        from committed_files
        where committed_files.commit_id = commits.sha
        and is_superfluous is true
    )
    where true
    """,
    """
    update commits
    set n_files_ignored = (
        select count(1)
        from committed_files
        where committed_files.commit_id = commits.sha
        and is_superfluous is true
    )
    where true
    """,
    "drop view if exists all_commit_data",
    """
        create view all_commit_data
        as
        select
            authors.id as author_id,
            authors.name,
            authors.email,
            authors.real_name,
            authors.real_email,
            authors.company,
            authors.team,
            authors.author_group,
            commits.sha,
            commits.created_at as commit_date,
            commits.created_ts as commit_date_ts,
            case commits.is_merge when true then 1 else 0 end as is_merge,
            commits.n_lines as commit_n_lines,
            commits.n_files as commit_n_files,
            commits.n_insertions as commit_n_insertions,
            commits.n_deletions as commit_n_deletions,
            commits.n_lines_changed as commit_n_lines_changed,
            commits.n_lines_ignored as commit_n_lines_ignored,
            commits.n_files_changed as commit_n_files_changed,
            commits.n_files_ignored as commit_n_files_ignored,
            committed_files.id as committed_file_id,
            committed_files.change_type,
            committed_files.file_path,
            committed_files.file_name,
            committed_files.file_type,
            committed_files.n_lines_added,
            committed_files.n_lines_deleted,
            committed_files.n_lines_changed,
            committed_files.n_lines_of_code,
            committed_files.n_methods,
            committed_files.n_methods_changed,
            committed_files.is_on_exclude_list,
            committed_files.is_superfluous,
            repo.repo_name,
            repo.repo_group,
            repo.repo_type,
            repo.component,
            repo.clone_url,
            repo.browse_url,
            repo.id as repo_id,
            repo.is_active as repo_inlude_in_stats,
            repo.last_indexed_at
        from authors
            inner join commits on commits.author_id = authors.id
            inner join committed_files on committed_files.commit_id = commits.sha
            inner join repo_to_commits rtc on commits.sha = rtc.commit_id
            inner join repositories repo on rtc.repo_id = repo.id
        """,  # convert is_merge to integer to make it compatible to the existing schema that I cannot change.
]


QUERY_SQL = {
    "all_commit_data": " select * from all_commit_data limit 1000000",
}
