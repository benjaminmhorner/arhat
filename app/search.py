from flask import current_app

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id,
                                    body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    #this is the problem, check elasticsearch docs for search terms allowing in a string
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        body={'query':  {'query_string': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    # f = open("C:/Users/ben.horner/Desktop/Test/MyFile.txt", "w")
    # f.write(str(query))
    # f.close
    return ids, search['hits']['total']