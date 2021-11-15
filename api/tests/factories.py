import factory

from models.Scan import Scan

# When adding new factories ensure you add the factory to the conftest session fixture so that they can be linked to the test db session


class ScanFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Scan

    id = factory.Faker("uuid4")
    name = factory.Faker("name")
    file_name = (factory.Faker("file_name"),)
    file_size = (factory.Faker("number"),)
    save_path = ("s3://foo.bar/baz",)
    sha256 = (factory.Faker("sha256"),)
    scan_provider = (factory.Faker("buzzword"),)
    submitter = (factory.Faker("name"),)
    verdict = ("clean",)
    quarantine_path = ("s3://foo.bar/fizz",)
    meta_data = {}
