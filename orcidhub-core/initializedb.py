from application import db
from model import Organisation, OrcidUser, UserRole

db.drop_all()
db.create_all()

addOrganisation = Organisation(org_name="The Royal Society of NewZealand", emailid="nzorcidhub@royalsociety.org.nz",
                               tuakiriname="The Royal Society of NewZealand",
                               orcid_client_id="client-123", orcid_secret="secret-123", confirmed=True)
superUser = OrcidUser(rname="The Royal Society of NewZealand", email="nzorcidhub@royalsociety.org.nz",
                      auedupersonsharedtoken="aaRtDix1l2z43M0vvWTBpBuf_ek", confirmed=True,
                      urole=UserRole.SUPERUSER, orgid="nzorcidhub@royalsociety.org.nz")

db.session.add(addOrganisation)
db.session.commit()
db.session.add(superUser)
db.session.commit()
