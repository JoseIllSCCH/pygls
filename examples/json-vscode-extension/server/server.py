############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
import asyncio
import json
import re
import time
import uuid
from json import JSONDecodeError
from typing import Optional
from rdflib import Graph
import yaml
import yamlLib.impl.ilo.YAML_ILOGraph as ILOTrans
import yamlLib.base.validation.SHACLFramework as SHACLFramework
import yamlLib.impl.HTTPOntologyService as dbservice
from pyshacl import validate
import sys

# sys.append("..")


from lsprotocol.types import (TEXT_DOCUMENT_COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                              TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN,
                              TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
from lsprotocol.types import (CompletionItem, CompletionList, CompletionOptions,
                              CompletionParams, ConfigurationItem,
                              Diagnostic,
                              DidChangeTextDocumentParams,
                              DidCloseTextDocumentParams,
                              DidOpenTextDocumentParams, MessageType, Position,
                              Range, Registration, RegistrationParams,
                              SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                              Unregistration, UnregistrationParams,
                              WorkDoneProgressBegin, WorkDoneProgressEnd,
                              WorkDoneProgressReport,
                              WorkspaceConfigurationParams)
from pygls.server import LanguageServer

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1


class ILOGraphLanguageServer(LanguageServer):
    CMD_COUNT_DOWN_BLOCKING = 'countDownBlocking'
    CMD_COUNT_DOWN_NON_BLOCKING = 'countDownNonBlocking'
    CMD_PROGRESS = 'progress'
    CMD_REGISTER_COMPLETIONS = 'registerCompletions'
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'
    CMD_UNREGISTER_COMPLETIONS = 'unregisterCompletions'
    CMD_MANUAL_SHACL_VALIDATION = 'validateNow'

    CONFIGURATION_SECTION = 'jsonServer'

    def __init__(self, *args):
        super().__init__(*args)


# KG Connection
service = dbservice.HTTPService("http://localhost:7200/repositories/SHACLTest/statements?")

# ILOGraph Specific Interfaces
iloIR = ILOTrans.ILOGraphToIntermediateModel()


# Generic interface to transform IR to ontology
irTransformation = ILOTrans.IntermediateToOntoFactory()

# SHACL Service
shaclService = SHACLFramework.LocalSHACLService()
shaclService.parseAll()

iloGraph_server = ILOGraphLanguageServer('pygls-json-example', 'v0.1')

# intialize the current classes found in the KG
classesList = asyncio.run(service.retrieveClasses())

# intialize the current classes found in the KG
opList = asyncio.run(service.retrieveObjectProperties())

# intialize the current classes found in the KG
instanceList = asyncio.run(service.retrieveInstances())

# shaclGraph= asyncio.run()

async def buildSHACLGraphFromLocalFIles():
    pass


def _validate(ls, params):
    ls.show_message_log('Validating ilograph...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _validate_ilo(ls, text_doc) if text_doc else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)



def _validate_ilo(ls, text_doc):
    """Validates yaml file."""
    diagnostics = []
    # if content is empty just return
    try:
        diagnostics= iloIR.iloValidator.validationResults(text_doc)
        if len(diagnostics)>0:
            return diagnostics

        # transform to IR
        iloIR.processData(text_doc)

        # check if intermediate model was succesfully created
        # TODO add a better way of communicating the error
        if not iloIR.isValid():
            # add error
            return diagnostics

        # transform to ontology
        onto = irTransformation.transformToOnto(iloIR)
        # apply shacl
        try:

            dGraph = Graph()
            dGraph.parse(data=onto)
            dGraph.parse("http://OHIO:7200/repositories/SHACLTest/rdf-graphs/service?default")
            sGraph = shaclService.getShapesGraph()

            validationResult = SHACLFramework.validateContent(dGraph, sGraph)
            conforms, results_graph, results_text = validationResult
            if not conforms:
                return SHACLFramework.prepareSHACLDiagnostics(ls, validationResult, text_doc)
        except Exception as err:
            diagnostics.append(ILOTrans.createDiagnostic(msg="Validation error",
                               src=type(iloGraph_server).__name__))
        # retrieve

        # print(data)

    except Exception as err:
        # diagnostics.append(createDiagnostic(
        #     msg="The provided yaml file does not fullfil the basic ILO graph structure.", src=type(iloGraph_server).__name__))
        print(err.problem_mark)
        diagnostics.append(ILOTrans.createDiagnostic(msg=err.problem, startLine=err.problem_mark.line, startChar=err.problem_mark.column,
                           endLine=err.problem_mark.line, endChar=err.problem_mark.column, src=type(iloGraph_server).__name__))

    return diagnostics


@iloGraph_server.feature(TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=[':']))
def completions(params: Optional[CompletionParams] = None) -> CompletionList:
    text_doc = iloGraph_server.workspace.get_document(params.text_document.uri)
    currentLine = text_doc.lines[params.position.line]
    print(currentLine)
    kind = iloIR.iloValidator.getKindOf(currentLine)
    if kind < 0:
        return []

    else:
        if kind == 0:
            # classes
            itemsKG = classesList
        elif kind == 1:
            # instances
            itemsKG = instanceList
        elif kind == 2:
            # relations
            itemsKG = opList
        else:
            return []

    return CompletionList(
        is_incomplete=False,
        # full IRI -> Short
        # items=[CompletionItem(label=x, insert_text=x[x.rindex("#")+1:])for x in classesList]
        # short -> Short
        items=[CompletionItem(label=" "+x[x.rindex("#")+1:])for x in itemsKG]
        # items=[
        #     CompletionItem(label='"'),
        #     CompletionItem(label='['),
        #     CompletionItem(label=']'),
        #     CompletionItem(label='{'),
        #     CompletionItem(label='}'),
        # ]
    ) if classesList != None else []


@iloGraph_server.command(ILOGraphLanguageServer.CMD_MANUAL_SHACL_VALIDATION)
def manual_validation(ls, *args):
    ls.show_message('Manual Validation should start... TODO')
    ls
    # _validate(ls, args)


@iloGraph_server.command(ILOGraphLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
    """Starts counting down and showing message synchronously.
    It will `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
        time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@iloGraph_server.command(ILOGraphLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
async def count_down_10_seconds_non_blocking(ls, *args):
    """Starts counting down and showing message asynchronously.
    It won't `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
        await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@iloGraph_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@iloGraph_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: ILOGraphLanguageServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@iloGraph_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)


@iloGraph_server.feature(
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    SemanticTokensLegend(
        token_types=["operator"],
        token_modifiers=[]
    )
)
def semantic_tokens(ls: ILOGraphLanguageServer, params: SemanticTokensParams):
    """See https://microsoft.github.io/language-server-protocol/specification#textDocument_semanticTokens
    for details on how semantic tokens are encoded."""

    TOKENS = re.compile('".*"(?=:)')

    uri = params.text_document.uri
    doc = ls.workspace.get_document(uri)

    last_line = 0
    last_start = 0

    data = []

    for lineno, line in enumerate(doc.lines):
        last_start = 0

        for match in TOKENS.finditer(line):
            start, end = match.span()
            data += [
                (lineno - last_line),
                (start - last_start),
                (end - start),
                0,
                0
            ]

            last_line = lineno
            last_start = start

    return SemanticTokens(data=data)


@iloGraph_server.command(ILOGraphLanguageServer.CMD_PROGRESS)
async def progress(ls: ILOGraphLanguageServer, *args):
    """Create and start the progress on the client."""
    token = str(uuid.uuid4())
    # Create
    await ls.progress.create_async(token)
    # Begin
    ls.progress.begin(token, WorkDoneProgressBegin(
        title='Indexing', percentage=0, cancellable=True))
    # Report
    for i in range(1, 10):
        # Check for cancellation from client
        if ls.progress.tokens[token].cancelled():
            # ... and stop the computation if client cancelled
            return
        ls.progress.report(
            token,
            WorkDoneProgressReport(message=f'{i * 10}%', percentage=i * 10),
        )
        await asyncio.sleep(2)
    # End
    ls.progress.end(token, WorkDoneProgressEnd(message='Finished'))


@iloGraph_server.command(ILOGraphLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: ILOGraphLanguageServer, *args):
    """Register completions method on the client."""
    params = RegistrationParams(registrations=[
        Registration(
            id=str(uuid.uuid4()),
            method=TEXT_DOCUMENT_COMPLETION,
            register_options={"triggerCharacters": "[':']"})
    ])
    response = await ls.register_capability_async(params)
    if response is None:
        ls.show_message('Successfully registered completions method')
    else:
        ls.show_message('Error happened during completions registration.',
                        MessageType.Error)


@iloGraph_server.command(ILOGraphLanguageServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: ILOGraphLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using coroutines."""
    try:
        config = await ls.get_configuration_async(
            WorkspaceConfigurationParams(items=[
                ConfigurationItem(
                    scope_uri='',
                    section=ILOGraphLanguageServer.CONFIGURATION_SECTION)
            ]))

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@iloGraph_server.command(ILOGraphLanguageServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: ILOGraphLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using callback."""
    def _config_callback(config):
        try:
            example_config = config[0].get('exampleConfiguration')

            ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

        except Exception as e:
            ls.show_message_log(f'Error ocurred: {e}')

    ls.get_configuration(
        WorkspaceConfigurationParams(
            items=[
                ConfigurationItem(
                    scope_uri='',
                    section=ILOGraphLanguageServer.CONFIGURATION_SECTION)
            ]
        ),
        _config_callback
    )


@iloGraph_server.thread()
@iloGraph_server.command(ILOGraphLanguageServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: ILOGraphLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using thread pool."""
    try:
        config = ls.get_configuration(WorkspaceConfigurationParams(items=[
            ConfigurationItem(
                scope_uri='',
                section=ILOGraphLanguageServer.CONFIGURATION_SECTION)
        ])).result(2)

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@iloGraph_server.command(ILOGraphLanguageServer.CMD_UNREGISTER_COMPLETIONS)
async def unregister_completions(ls: ILOGraphLanguageServer, *args):
    """Unregister completions method on the client."""
    params = UnregistrationParams(unregisterations=[
        Unregistration(id=str(uuid.uuid4()), method=TEXT_DOCUMENT_COMPLETION)
    ])
    response = await ls.unregister_capability_async(params)
    if response is None:
        ls.show_message('Successfully unregistered completions method')
    else:
        ls.show_message('Error happened during completions unregistration.',
                        MessageType.Error)
