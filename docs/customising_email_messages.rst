.. _customising_email_messages:

Customising your email messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

UI Changes Since V2
+++++++++++++++++++

"**Your organisation**" has been replaced with "**Settings**", and underneath the new "**Settings**" dropdown you can now find:

- "**Your organisation**"
- "**Logo**", and
- "**Email template**"

Any *.jpg* or *.png* can be uploaded by selecting "**Logo**" and using the options on the resulting page.  If you're prepared to put some effort into altering your email template then the options are very open, but for the simplest substitution please start with a picture that's **127 pixels high** as it'll will drop right into the space occupied by the default Society logo.

Next from the "**Email template**" page you are given the option of toggling the "**Email template enabled**" option.

Once enabled, a blank document is opened where you can enter the html for the mail that the Hub sends on your behalf.

As that might be a little daunting, to start with (and perhaps doing all that you require) press the "**Prefill**" button to copy the default html for the Hub's messages and edit from there.

There are three merged fields that may be of use:

- **{EMAIL}**: Recipient email address
- **{LOGO}**: Organisation logo
- **{MESSAGE}**: Core message that will be sent to the recipient

The {MESSAGE} field is customised for each type of mail that the Hub sends, e.g., invitation, affiliation invite, funding invite, reminders and revoked permission repeat request.
If you don't include this in the template the Hub will send the same message in all instances.

When you think you've got something that works, pressing "Send" will email you a test message with the current template.  If that's what you want, press save and any subsequent messages will be style with your new template.

If you ever want to go back to the default Society-style, just toggle off "**Email template enabled**".
