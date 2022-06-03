# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

import requests
import zeep
from zeep.wsse.username import UsernameToken

FILE_PATH = os.path.dirname(__file__)
PROD_URL = "https://ebill.postfinance.ch/B2BService/B2BService.svc"
PROD_CERT = os.path.join(FILE_PATH, "certificates", "prod", "SwissSign_Gold_CA-G2.cer")
PROD_WSDL = os.path.join(FILE_PATH, "wsdl", "b2bservice_prod.wsdl")
TEST_URL = "https://ebill-ki.postfinance.ch/B2BService/B2BService.svc"
TEST_CERT = os.path.join(FILE_PATH, "certificates", "inte", "SwissSign_Gold_CA-G2.cer")
TEST_WSDL = os.path.join(FILE_PATH, "wsdl", "b2bservice_inte.wsdl")


class WebService:
    def __init__(
        self, test_service, username, password, biller_id, operation_timeout=None
    ):
        self.use_test_service = True
        settings = zeep.Settings(xml_huge_tree=True)
        session = requests.Session()
        if test_service:
            session.verify = TEST_CERT
            wsdl_doc = TEST_WSDL
            url = TEST_URL
        else:
            wsdl_doc = PROD_WSDL
            session.verify = PROD_CERT
            url = PROD_URL
        transport = zeep.transports.Transport(
            session=session, operation_timeout=operation_timeout
        )
        self.client = zeep.Client(
            wsdl_doc,
            transport=transport,
            settings=settings,
            wsse=UsernameToken(username, password),
        )
        self.service = self.client.create_service(
            "{http://ch.swisspost.ebill.b2bservice}UserNamePassword", url
        )
        self.biller_id = biller_id

    def ping(self, test_error=False, test_exception=False):
        res = self.service.ExecutePing(
            BillerID=self.biller_id, ErrorTest=test_error, ExceptionTest=test_exception
        )
        return res

    def upload_files(self, transaction_id, file_type, data):
        """Call UploadFilesReport

        This is used to upload invoices for biller.
        It accepts multiple invoices, but only one is passed at the moment.
        """
        invoice_type = self.client.get_type("ns2:Invoice")
        array_invoice_type = self.client.get_type("ns2:ArrayOfInvoice")
        invoice = invoice_type(
            TransactionID=transaction_id, FileType=file_type, Data=data
        )
        invoices = array_invoice_type(invoice)
        res = self.service.UploadFilesReport(BillerID=self.biller_id, invoices=invoices)
        return res

    def search_invoices(self, transaction_id=None):
        parameter_type = self.client.get_type("ns2:SearchInvoiceParameter")
        parameters = parameter_type(
            BillerID=self.biller_id, TransactionID=transaction_id
        )
        res = self.service.SearchInvoices(Parameter=parameters)
        return res

    def initiate_ebill_recipient_subscription(self, recipient_email):
        """Start the subscription for an ebill recipient.

        recipient_email: email of the recipient

        response:{
            SubscriptionInitiationToken: initiation token to use for confirmation
            Message: None
        }
        """
        res = self.service.InitiateEBillRecipientSubscription(
            BillerID=self.biller_id, SubscriptionInitiationEmailAddress=recipient_email
        )
        return res

    def confirm_ebill_recipient_subscription(self, initiation_token, activation_code):
        """Confirm the subscription of an ebill recipient.

        initiation_token: token received at the initiation api call
        activation_code: code provided by the user

        response: could not get to this point yet!

        """
        res = self.service.ConfirmEBillRecipientSubscription(
            BillerID=self.biller_id,
            SubscriptionInitiationToken=initiation_token,
            SubscriptionInitiationActivationCode=activation_code,
        )
        return res

    def get_ebill_recipient_subscription_status(self, recipient_id):
        """Returns information if invoices can be sent to one eBill recipient.

         recipient_id: the ebill payer id, email address or UIDHR

         response: [{
            EbillAccountID: payer id returned if relation is agreed on.
            EmailAddress: email if used in search
            UIDHR: enterprise id number if used in search
            Message: Error message if any.
        }]
        """
        res = self.service.GetEBillRecipientSubscriptionStatus(
            BillerID=self.biller_id, RecipientID=recipient_id
        )
        return res

    def get_ebill_recipient_subscription_status_bulk(self, bill_recipient_id):
        """Returns information if invoices can be sent to a list of eBill recipients.

         recipient_id: a list of ebill recipient id, email address or UIDHR

        """
        array_bill_recipient = self.client.get_type("ns2:ArrayOfBillRecipient")
        recipients = array_bill_recipient(bill_recipient_id)

        res = self.service.GetEBillRecipientSubscriptionStatusBulk(
            BillerID=self.biller_id, RecipientID=recipients
        )
        # An error occurs, maybe because the response is badly formatted ?
        # zeep.exceptions.ValidationError:
        #     Missing element SubmissionStatus
        #     (GetEBillRecipientSubscriptionStatusBulk.RecipientID.BillRecipient)
        return res

    def get_invoice_list(self, archive_data=False):
        """Returns a list of available invoices for a Biller

        archieved_data: include already downloaded data if true

        response: list of zeep.objects.InvoiceReport
            {
                BillerID:  the biller id
                TransactionID: transaction id from the upload
                DeliveryDate: upload date of the invoice
                FileType: file type
            }

        """
        res = self.service.GetInvoiceListBiller(
            BillerID=self.biller_id, ArchiveData=archive_data
        )
        return res

    def get_invoice_biller(self, transaction_id, bill_detail):
        """Download an invoice for a biller.

        transaction_id: the transaction id of the wanted invoice
        bill_detail: true=download BillDetail pdf, false=download invoice only

        response: a list of DownloadFile

        """
        # Raised an error when tested
        #   File "src/lxml/apihelpers.pxi", line 1734,
        #         in lxml.etree._tagValidOrRaise
        #   ValueError: Invalid tag name '005'
        res = self.service.GetInvoiceBiller(
            BillerID=self.biller_id,
            TransactionID=transaction_id,
            BillDetail=bill_detail,
        )
        return res

    def get_process_protocol_list(self, archive_data=False):
        """Returns a list of available process protocol (log from invoice upload)

        archieved_data: include already downloaded data if true

        response: list of zeep.objects.ProtocolReport
            {
                CreateDate: datetime of the report creation
                FileType: 'P' ? could be different ?
            }
        """
        res = self.service.GetProcessProtocolList(
            BillerID=self.biller_id, ArchiveData=archive_data
        )
        return res

    def get_process_protocol(self, create_date, archive_data=False):
        """Returns a process protocol file data.

        create_date: create date of the protocol to download
        archieved_data: include already downloaded data if true

        response: a list of zeep.objects.DownloadFile (should be only one ?)
            {
                Data: content of the file in bytes
                Filename: name of the xml file
            }

        """
        res = self.service.GetProcessProtocol(
            BillerID=self.biller_id, CreateDate=create_date, ArchiveData=archive_data
        )
        return res

    def get_registration_protocol_list(self, archive_data=False):
        """Returns a list of available logs from subscription process.

        archieved_data: include already downloaded data if true

        response: I could not generate any of those in testing.

        """
        res = self.service.GetRegistrationProtocolList(
            BillerID=self.biller_id, ArchiveData=archive_data
        )
        return res

    def get_registration_protocol(self, create_date, archive_data):
        """Returns the file data of a subscription process log.

        create_date: create date of the protocol to download
        archieved_data: include already downloaded data if true

        response: I could not test that.

        """
        res = self.service.GetRegistrationProtocol(
            BillerID=self.biller_id, CreateDate=create_date, ArchiveData=archive_data
        )
        return res
