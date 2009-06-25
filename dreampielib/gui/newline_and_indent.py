__all__ = ['newline_and_indent']

from . import PyParse

def newline_and_indent(sourceview, INDENT_WIDTH):
    """
    Get a sourceview. Add a newline and indent - what happens when the user
    pressed Enter.
    """
    # This is based on newline_and_indent_event(),
    # from idlelib/EditorWindow.py
    sb = sourceview.get_buffer()
    sb.begin_user_action()
    insert_mark = sb.get_insert()
    insert = lambda: sb.get_iter_at_mark(insert_mark)
    try:
        sb.delete_selection(True, True)
        line = sb.get_text(sb.get_iter_at_line(insert().get_line()),
                           insert())
        i, n = 0, len(line)
        while i < n and line[i] in " \t":
            i = i+1
        if i == n:
            # the cursor is in or at leading indentation in a continuation
            # line; just copy the indentation
            sb.insert_at_cursor('\n'+line)
            sourceview.scroll_mark_onscreen(sb.get_insert())
            return True
        indent = line[:i]
        # strip whitespace before insert point
        i = 0
        while line and line[-1] in " \t":
            line = line[:-1]
            i = i+1
        if i:
            sb.delete(sb.get_iter_at_line_offset(insert().get_line(),
                                                 len(line)),
                      insert())
        # strip whitespace after insert point
        it = insert(); it.forward_to_line_end()
        after_insert = sb.get_text(insert(), it)
        i = 0
        while i < len(after_insert) and after_insert[i] in " \t":
            i += 1
        if i > 0:
            it = insert(); it.forward_chars(i)
            sb.delete(insert(), it)
        # start new line
        sb.insert_at_cursor('\n')
        # scroll to see the beginning of the line
        sourceview.scroll_mark_onscreen(sb.get_insert())
        #self.scrolledwindow_sourceview.get_hadjustment().set_value(0)

        # adjust indentation for continuations and block
        # open/close first need to find the last stmt
        y = PyParse.Parser(INDENT_WIDTH, INDENT_WIDTH)
        y.set_str(sb.get_text(sb.get_start_iter(), insert()))
        c = y.get_continuation_type()
        if c != PyParse.C_NONE:
            # The current stmt hasn't ended yet.
            if c == PyParse.C_STRING_FIRST_LINE:
                # after the first line of a string; do not indent at all
                pass
            elif c == PyParse.C_STRING_NEXT_LINES:
                # inside a string which started before this line;
                # just mimic the current indent
                sb.insert_at_cursor(indent)
            elif c == PyParse.C_BRACKET:
                # line up with the first (if any) element of the
                # last open bracket structure; else indent one
                # level beyond the indent of the line with the
                # last open bracket
                sb.insert_at_cursor(' ' * y.compute_bracket_indent())
            elif c == PyParse.C_BACKSLASH:
                # if more than one line in this stmt already, just
                # mimic the current indent; else if initial line
                # has a start on an assignment stmt, indent to
                # beyond leftmost =; else to beyond first chunk of
                # non-whitespace on initial line
                if y.get_num_lines_in_stmt() > 1:
                    sb.insert_at_cursor(indent)
                else:
                    sb.insert_at_cursor(' ' * y.compute_backslash_indent())
            else:
                assert False, "bogus continuation type %r" % (c,)
            return True

        # This line starts a brand new stmt; indent relative to
        # indentation of initial line of closest preceding
        # interesting stmt.
        indent = len(y.get_base_indent_string())
        if y.is_block_opener():
            indent = (indent // INDENT_WIDTH + 1) * INDENT_WIDTH
        elif y.is_block_closer():
            indent = max(((indent - 1) // INDENT_WIDTH) * INDENT_WIDTH, 0)
        sb.insert_at_cursor(' ' * indent)
        return True
    finally:
        sb.end_user_action()

