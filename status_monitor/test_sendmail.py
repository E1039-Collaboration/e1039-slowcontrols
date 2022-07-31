#!/usr/bin/env python
import DAQUtils

recipients = [ "bhy7tf@virginia.edu" ]
subject = "Test message by test_sendmail.py"
message = "Test message."
DAQUtils.SendMail(recipients, subject, message=message)
