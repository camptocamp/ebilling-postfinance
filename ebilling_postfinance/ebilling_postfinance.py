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
        res = self.service.InitiateEBillRecipientSubscription(
            BillerID=self.biller_id,
            SubscriptionInitiationEmailAddress=recipient_email,
        )
        return res

    def get_ebill_recipient_subscription_status(self, recipient_id):
        res = self.service.GetEBillRecipientSubscriptionStatus(
            BillerID=self.biller_id,
            RecipientID=recipient_id,
        )
        return res

    # Not used
    def get_invoice_list(self, archive_data=False):
        res = self.service.GetInvoiceListBiller(
            BillerID=self.biller_id,
            ArchiveData=archive_data,
        )
        return res

    def get_process_protocol_list(self, archive_data=False):
        res = self.service.GetProcessProtocolList(
            BillerID=self.biller_id,
            ArchiveData=archive_data,
        )
        return res

    def get_registration_protocol_list(self, archive_data=False):
        res = self.service.GetRegistrationProtocolList(
            BillerID=self.biller_id,
            ArchiveData=archive_data,
        )
        return res

    def get_registration_protocol(self, create_date, archive_data):
        # res = self.service.GetRegistrationProtocol(
        #     BillerID=self.biller_id,
        #     CreateDate=create_date,
        #     ArchiveData=archive_data,
        # )
        res = "not implemented"
        return res
