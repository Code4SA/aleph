from __future__ import absolute_import
import logging
from polyglot.downloader import downloader

from aleph import graph
from aleph.core import celery, db
from aleph.ext import get_analyzers
from aleph.model import Document
from aleph.index import index_document
from aleph.search import scan_iter


log = logging.getLogger(__name__)


def install_analyzers():
    # ['pos2', 'ner2', 'morph2', 'tsne2', 'counts2', 'embeddings2',
    #  'sentiment2', 'sgns2', 'transliteration2']
    for task in ['embeddings2', 'ner2']:
        log.info("Downloading linguistic resources: %r...", task)
        downloader.download('TASK:%s' % task, quiet=True)


def analyze_documents(collection_id):
    query = {'term': {'collection_id': collection_id}}
    query = {'query': query, '_source': False}
    for row in scan_iter(query):
        analyze_document_id.delay(row.get('_id'))


@celery.task()
def analyze_document_id(document_id):
    document = Document.by_id(document_id)
    if document is None:
        log.info("Could not find document: %r", document_id)
        return
    analyze_document(document)


def analyze_document(document):
    log.info("Analyze document: %r", document)
    analyzers = []
    meta = document.meta
    log.debug("Loading analyzers")
    for cls in get_analyzers():
        analyzer = cls(document, meta)
        analyzer.prepare()
        analyzers.append(analyzer)

    for i, text in enumerate(document.text_parts()):
        for analyzer in analyzers:
            log.debug("Applying %r on text part %d", analyzer, i)
            analyzer.on_text(text)

    log.debug("Finalizing analyzers")
    for analyzer in analyzers:
        analyzer.finalize()
    document.meta = meta
    db.session.add(document)
    db.session.commit()
    index_document(document)
    with graph.transaction() as tx:
        graph.load_document(tx, document)
