var loadCollection = ['$route', 'Collection', function($route, Collection) {
  var collectionId = $route.current.params.collection_id;
  return Collection.get(collectionId);
}];

var loadCollectionDocuments = ['$route', 'Document', function($route, Document) {
  var collectionId = $route.current.params.collection_id;
  return Document.search(collectionId);
}];

var loadCollectionEntities = ['$route', 'Entity', function($route, Entity) {
  var collectionId = $route.current.params.collection_id;
  return Entity.searchCollection(collectionId);
}];
