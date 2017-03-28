import models
from models import Organisation, User, Role

models.drop_tables()
models.create_tables()

org0 = Organisation(
    name="The Royal Society of NewZealand",
    email="nzorcidhub@royalsociety.org.nz",
    tuakiri_name="The Royal Society of NewZealand",
    orcid_client_id="client-123",
    orcid_secret="secret-123",
    confirmed=True)
org0.save()

super_user = User(
    name="The Royal Society of NewZealand",
    email="nzorcidhub@royalsociety.org.nz",
    edu_person_shared_token="aaRtDix1l2z43M0vvWTBpBuf_ek",
    confirmed=True,
    roles=Role.SUPERUSER)
super_user.save()

super_user = User(
    name="The Root",
    email="root@mailinator.com",
    confirmed=True,
    roles=Role.SUPERUSER)
super_user.save()
