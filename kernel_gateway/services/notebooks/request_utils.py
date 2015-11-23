import json

def body_to_json(body):
    '''Converts body into a proper JSON string. body is expected to be a UTF-8
    byte string. If body is the empty string or None, the empty string will be
    returned.
    '''
    body.decode(encoding='UTF-8')
    if body is not None and body is not '':
        return json.loads(body)
    else:
        return ''


def args_to_json(args):
    '''Converts args into a proper JSON string. args is expected to be a dictionary
    where the values are arrays of UTF-8 byte strings.
    '''
    ARGS = {}
    for key in args:
        ARGS[key] = []
        for value in args[key]:
            ARGS[key].append(value.decode(encoding='UTF-8'))
    return json.dumps(ARGS)
