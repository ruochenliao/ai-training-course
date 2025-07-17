import json
import csv
import os
import datasets

logger = datasets.logging.get_logger(__name__)

_DESCRIPTION = "RAR-b TempReason-l3-context Dataset"
_SPLITS = ["corpus", "queries", "qrels"]

URL = ""
_URLs = {subset: URL + f"{subset}.jsonl" if subset != "qrels" else URL + f"qrels/test.tsv" for subset in _SPLITS}

class RARb(datasets.GeneratorBasedBuilder):
    """RAR-b BenchmarkDataset."""

    BUILDER_CONFIGS = [
        datasets.BuilderConfig(
            name=name,
            description=f"This is the {name} in the RAR-b TempReason-l3-context dataset.",
        ) for name in _SPLITS
    ]
    DEFAULT_CONFIG_NAME = "qrels"
    
    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features({
                "_id": datasets.Value("string"), 
                "title": datasets.Value("string"),
                "text": datasets.Value("string"),
            }) if self.config.name != "qrels" else datasets.Features({
                "query-id": datasets.Value("string"),
                "corpus-id": datasets.Value("string"),
                "score": datasets.Value("int32"),
            }),
            supervised_keys=None,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        if self.config.name == "qrels":
            test_url = URL + "qrels/test.tsv"
            test_path = dl_manager.download_and_extract(test_url)
            return [
                datasets.SplitGenerator(
                    name=datasets.Split.TEST,
                    gen_kwargs={"filepath": test_path},
                ),
            ]
        else:
            my_urls = _URLs[self.config.name]
            data_dir = dl_manager.download_and_extract(my_urls)
            return [
                datasets.SplitGenerator(
                    name=self.config.name,
                    gen_kwargs={"filepath": data_dir},
                ),
            ]

    def _generate_examples(self, filepath):
        """Yields examples."""
        if self.config.name == "qrels":
            with open(filepath, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader) # skip header row
                for i, row in enumerate(reader):
                    yield i, {
                        "query-id": row[0],
                        "corpus-id": row[1],
                        "score": int(row[2]),
                    }
        else:
            with open(filepath, encoding="utf-8") as f:
                texts = f.readlines()
            for i, text in enumerate(texts):
                text = json.loads(text)
                if 'metadata' in text: del text['metadata']
                if "title" not in text: text["title"] = ""
                yield i, text
