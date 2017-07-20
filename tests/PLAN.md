# Authentication via TUAKIRI (__Any Users__)

 - New user (creates an entry in user table, link to the organisation entry);
 - Returning user;
 - Returning user after update IdP (IAM) profile, e.g., preferred name, affiliation nature (staff, student, etc.);
 - Returning user after update IdP (IAM) profile: email address;
 - Entering invalid data (all kinds of corner cases);

# Organisation on-boarding (organisation invitation to join the Hub) (__Hub Admin__)

 - Sending invitation to a user not yet registered;
 - Sending invitation to an exiting user;
 - Re-sending an invitation (generating a new token);
 - Entering invalid data (all kinds of corner cases);


 # Organisation on-boarding (adding organisation credentials to the Hub) (__Org.Admin__)
 - Attempt to re-use the invitation token;
 - Entering invalid data (all kinds of corner cases);

# Organisation administrator invitation (__Hub Admin__)

 - Sending invitation to a user not yet registered;
 - Sending invitation to an exiting user;
 - Re-sending an invitation (generating a new token);
 - Attempt to re-use the invitation token;

# User/Researcher affiliation (__Any User__)

# User profile update (adding new entries, deletion and update of records) (__Org.Admin__)

# Supporting Functionality

 - Organisation information import (__Hub.Admin__);
 - User Summary (__Hub.Admin__);
 - Invitation Summary (__Hub.Admin__).
