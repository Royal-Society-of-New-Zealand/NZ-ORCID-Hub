# Currently Implemented
 - Login of a User;
 - New user (creates an entry in user table, link to the organisation entry);
 - Returning user;
 - Entering invalid data (all kinds of corner cases);
 - Creation & Removal of Organisation

# Organisation on-boarding (organisation invitation to join the Hub) (_Hub Admin_)
 - Sending invitation to a user not yet registered;
 - Sending invitation to an exiting user;
 - Re-sending an invitation (generating a new token);
 - Entering invalid data (all kinds of corner cases);

# Organisation on-boarding (adding organisation credentials to the Hub) (_Org.Admin_)
 - Attempt to re-use the invitation token;
 - Entering invalid data (all kinds of corner cases);

# Organisation administrator invitation (_Hub Admin_)
 - Sending invitation to a user not yet registered;
 - Sending invitation to an exiting user;
 - Re-sending an invitation (generating a new token);
 - Attempt to re-use the invitation token;

# Organisation (not connected to TUAKIRI) administrator invitation (_Hub Admin_)
 - Sending invitation to a user not yet registered;
 - Sending invitation to an exiting user;
 - Re-sending an invitation (generating a new token);
 - Attempt to re-use the invitation token;

# User/Researcher affiliation (_Any User_)

# User profile update (adding new entries, deletion and update of records) (_Org.Admin_)

# Supporting Functionality
 - Organisation information import (_Hub.Admin_);
 - User Summary (_Hub.Admin_);
 - Invitation Summary (_Hub.Admin_).

# Difficult Tests to be added
 - Returning user after update IdP (IAM) profile, e.g., preferred name, affiliation nature (staff, student, etc.);
 - Returning user after update IdP (IAM) profile: email address;
