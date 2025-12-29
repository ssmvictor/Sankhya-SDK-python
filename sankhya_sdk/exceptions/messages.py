# -*- coding: utf-8 -*-
"""
This module contains the error messages used by the custom exceptions in the Sankhya SDK.
"""

# Authentication/Authorization messages
SERVICE_REQUEST_INVALID_AUTHORIZATION = "Attempt of unauthorized/unauthenticated access"
SERVICE_REQUEST_INVALID_CREDENTIALS = "Unable to authenticate in Sankhya web service with provided credentials data"
SERVICE_REQUEST_EXPIRED_AUTHENTICATION = "The user's session is expired"

# Service Request messages
SERVICE_REQUEST_GENERAL = "A general error occurred during the service request"
SERVICE_REQUEST_TIMEOUT = "The call to the {0} service has timed out"
SERVICE_REQUEST_PROPERTY_NAME = "The call to the service {0} couldn't find the field {1} on entity {2} in {3} entity request"
SERVICE_REQUEST_PROPERTY_VALUE = "The call to the service {0} couldn't find the field {1} on entity {2}"
SERVICE_REQUEST_PROPERTY_WIDTH = "The call to the service {0} couldn't be completed because the width of the value for the {1} property on entity {2} is above that allowed. Current width: {3}. Width allowed: {4}"
SERVICE_REQUEST_ATTRIBUTE = "The service {0} requires the attribute {1}"
SERVICE_REQUEST_BUSINESS_RULE_RESTRICTION = "The business rule {0} doesn't allow the request to be completed. Error message: {1}"
SERVICE_REQUEST_CANCELED_QUERY = "Query canceled, probably overloaded on server. Taking {0} seconds to retry."
SERVICE_REQUEST_EXTERNAL = "Internal Sankhya error (NPE) on call to the {0} service. Check Sankhya log file for more information"
SERVICE_REQUEST_FOREIGN_KEY = "The value supplied to {0}.{1} reference isn't valid."
SERVICE_REQUEST_FILE_NOT_FOUND = "Unable to load the file from path {0}. File or directory not found."
SERVICE_REQUEST_INACCESSIBLE = "Unable to connect to Sankhya server at address {0}:{1}"
SERVICE_REQUEST_INVALID_EXPRESSION = "The filter expression '{0}' is invalid, check if it is a valid SQL expression!"
SERVICE_REQUEST_INVALID_SUBQUERY = "The subquery returned more than 1 value. This is not allowed when the subquery follows a =,! =, <, <=,>,> = or when it is used as an expression"
SERVICE_REQUEST_PARTNER_INVALID_DOCUMENT_LENGTH = "The partner document have an invalid length"
SERVICE_REQUEST_PARTNER_STATE_INSCRIPTION = "Enter the word ISENTO for this type of state registration"
SERVICE_REQUEST_PARTNER_FISCAL_CLASSIFICATION = "In the absence of the State registration, only the ICMS Classification: 'Non - Contributing Final Consumer' and 'Rural Producer' are permitted"

# Advanced Service Request messages
SERVICE_REQUEST_REPEATED = "You can not use a managed request object that was already consumed"
SERVICE_REQUEST_PAGINATION = "Unable to complete the paged request, concurrent requests from the same user causes this error"
SERVICE_REQUEST_TOO_MANY_RESULTS = "The request to {0} service on entity {1} resulted in {2} entities as a result. The expected was only one entity"
SERVICE_REQUEST_UNAVAILABLE = "The call to the {0} service is currently unavailable"
SERVICE_REQUEST_UNBALANCED_DELIMITER = "There is an unbalanced delimiter in the request"
SERVICE_REQUEST_UNEXPECTED_RESULT = "The call to the {0} service resulted in an invalid response"
SERVICE_REQUEST_UNEXPECTED_RESULT_UNCAUGHT = "The call to the {0} service resulted in the following uncaught error message: {1}"
SERVICE_REQUEST_DUPLICATED_DOCUMENT = "The partner {0} has the document duplicated with another partner"
SERVICE_REQUEST_FULL_TRANSACTION_LOGS = "The transaction logs of '{0}' database is full"
SERVICE_REQUEST_INVALID_RELATION = "The relation {0} of entity {1} cannot be found on Sankhya"
SERVICE_REQUEST_INVALID_OPERATION = "Unable to process the service response"
SERVICE_REQUEST_COMPETITION = "A competition/concurrency error occurred during the service request"
SERVICE_REQUEST_DEADLOCK = "A deadlock occurred during the transaction"

# Operation specific messages
CONFIRM_INVOICE = "Unable to confirm invoice with single number: {0}"
NO_ITEMS_CONFIRM_INVOICE = "Invoice {0} has no items, cannot be confirmed"
REMOVE_INVOICE = "Unable to remove invoice with single number: {0}"
MARK_AS_PAYMENT_PAID = "Unable to low payments for financial numbers {0}"
UNLINK_SHIPPING = "Unable to unlink shipping for financial numbers {0}"
PAGED_REQUEST = "There were one or more errors in the paged request below"
INVALID_SERVICE_QUERY_OPTIONS = "Unable to use query options with service {0}"
INVALID_SERVICE_REQUEST_OPERATION = "Unable to execute this operation with service {0}"
MISSING_SERIALIZER_HELPER_ENTITY = "The {0} property of {1} entity (Type: {2}) is missing the serializer helper method"
OPEN_FILE = "Unable to open the file with the key {0} in the Sankhya file manager"
SERVICE_RESPONSE_UNEXPECTED_ELEMENT = "The '{0}' element is not currently being addressed in Service Response.ResponseBody for the {1} service"

# Simple exceptions
INVALID_KEY_FILE = "The supplied key {0} is not valid for this session or has been deleted from the Sankhya"
CANCELLED_ON_DEMAND_REQUEST_WRAPPER = "Cannot add new items to a cancelled on demand request wrapper instance"
TOO_INNER_LEVELS = "Too many inner levels for entity {0}" # Guessing message, as I didn't see it clearly in .resx
