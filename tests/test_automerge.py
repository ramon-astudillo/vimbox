import copy
import sys
from tools import green, run_in_environment
from vimbox.remote.primitives import automerge


def test_main():

    # AUTOMERGE: Append
    local_content = 'This is some text'
    remote_content = local_content + "\nAppended line"
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'append', 'prepend'}
    )
    assert merge_strategy == 'append', "Automerge appended line failed"
    assert merged_content == remote_content, "Automerge appended line failed"
    print("Automerge append %s" % green("OK"))

    # AUTOMERGE: Append-line
    local_content = 'This is some text'
    remote_content = local_content + "Appended to line"
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'line-append'}
    )
    assert merge_strategy == 'line-append', "Automerge appended line failed"
    assert merged_content == remote_content, "Automerge appended line failed"
    print("Automerge line append %s" % green("OK"))

    # AUTOMERGE: Prepend
    local_content = 'This is some text'
    remote_content = 'Prepended text\n' + local_content
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'append', 'prepend'}
    )
    assert merge_strategy == 'prepend', "Automerge prepended failed"
    assert merged_content == remote_content, "Automerge prepend failed"
    print("Automerge prepend %s" % green("OK"))

    # AUTOMERGE: Prepend
    local_content = 'This is some text'
    remote_content = 'Prepended to line' + local_content
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'line-prepend'}
    )
    assert merge_strategy == 'line-prepend', "Automerge prepended line failed"
    assert merged_content == remote_content, "Automerge prepend line failed"
    print("Automerge line prepend %s" % green("OK"))

    # AUTOMERGE: Insert
    local_lines = ['This is one sentence', 'This is another']
    remote_lines = list(local_lines)
    remote_lines.insert(1, 'Inserted 1')
    remote_lines.insert(2, 'Inserted 2')
    remote_lines.insert(4, 'Inserted 3')
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'insert'}
    )
    assert merge_strategy == 'insert', "Automerge prepended line failed"
    assert merged_content == remote_content, "Automerge insert line failed"
    print("Automerge insert %s" % green("OK"))

    # AUTOMERGE: Valid line modification
    local_lines = ['this is one sentence', 'this is another']
    remote_lines = ['this is two sentences', 'this is another']
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {'ignore-edit': '(.* is).*(sentence)s?'}
    )
    assert merge_strategy == 'ignore-edit', "Automerge ignore-edit failed"
    assert merged_content == remote_content, "Automerge ignore-edit failed"
    print("Automerge ignore-edit %s" % green("OK"))

    # AUTOMERGE: Multiple cases
    local_lines = ['this is one sentence', 'this is another']
    remote_lines = [
        'this is two sentences',
        'I inserted something here',
        'prepended stuff this is another'
    ]
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = automerge(
        local_content,
        remote_content,
        {
            'ignore-edit': '(.* is).*(sentence)s?',
            'insert': True,
            'line-prepend': True
        }
    )
    assert sorted(merge_strategy.split('+')) == [
        'ignore-edit', 'insert', 'line-prepend'
    ], "Automerge ignore-edit failed"
    assert merged_content == remote_content, "Automerge ignore-edit failed"
    print("Automerge ignore-edit %s" % green("OK"))


if __name__ == '__main__':
    run_in_environment(test_main, backend_name='fake', debug=True)
