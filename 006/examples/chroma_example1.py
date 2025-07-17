from chromadb.utils import embedding_functions
default_ef = embedding_functions.DefaultEmbeddingFunction()
val = default_ef(["但问智能欢迎您"])
print(val) #
