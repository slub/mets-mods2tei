"""
multi-purpose METS editing and file handling tool purposed for DFG Viewer
"""
from __future__ import absolute_import

import os
import sys
from pathlib import Path
from datetime import datetime
import click
#from lxml.isoschematron import Schematron
from lxml import etree as ET
from ocrd.decorators import ocrd_loglevel
from ocrd import Resolver, Workspace, WorkspaceValidator, WorkspaceBackupManager
from ocrd_utils import getLogger, initLogging, remove_non_path_from_url, MIME_TO_EXT, VERSION
#from ocrd_models import OcrdXmlDocument
from ocrd_models import OcrdMets, OcrdAgent
from ocrd_models.constants import (
    NAMESPACES as NS,
    TAG_METS_FLOCAT,
    TAG_METS_FILE,
    TAG_METS_AGENT,
    TAG_METS_METSHDR
)


class WorkspaceCtx():

    def __init__(self, directory, mets_url, automatic_backup):
        self.log = getLogger('mets_mods2tei.update')
        self.resolver = Resolver()
        self.directory, self.mets_url, self.mets_basename = self.resolver.resolve_mets_arguments(directory, mets_url, None)
        self.automatic_backup = automatic_backup

pass_workspace = click.make_pass_decorator(WorkspaceCtx)



@click.group()
@click.version_option()
@ocrd_loglevel
@click.option('-d', '--directory', envvar='WORKSPACE_DIR', type=click.Path(file_okay=False), metavar='WORKSPACE_DIR', help='Changes the workspace folder location [default: METS_URL directory or .]"')
@click.option('-m', '--mets', default=None, help='The path/URL of the METS file [default: WORKSPACE_DIR/mets.xml]', metavar="METS_URL")
@click.option('--backup', default=False, help="Backup METS whenever it is saved.", is_flag=True)
@click.pass_context
def cli(ctx, directory, mets, backup, **kwargs): # pylint: disable=unused-argument
    """
    Entry-point of multi-purpose CLI for DFG Viewer compliant METS updates
    """
    initLogging()
    ctx.obj = WorkspaceCtx(directory, mets_url=mets, automatic_backup=backup)

@cli.command('download')
@click.option('-G', '--file-grp', help="fileGrp USE (or empty if all fileGrps)", default=None, metavar='FILE_GRP')
@click.option('-g', '--page-id', help="ID of the physical page (or empty if all pages)", default=None, metavar='PAGE_ID')
@click.option('-p', '--path-names', help="how to generate local path names (from URL or from fileGrp, file ID and suffix)", show_default=True,
              type=click.Choice(['URL', 'GRP/ID.SUF']), default='URL')
@click.option('-u', '--url-prefix', help="URL prefix to remove from path before storing downloaded files (to avoid creating host directories)", required=False)
@click.option('-r', '--reference', help="whether and how to update the FLocat reference in METS", show_default=True,
              type=click.Choice(['no-change', 'replace-by-local', 'insert-local', 'append-local']), default='no-change')
@pass_workspace
def download_cli(ctx, file_grp, page_id, path_names, url_prefix, reference):
    """
    download files into subdirectories, as path or URL
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    files = list(workspace.find_files(file_grp=file_grp, page_id=page_id))
    ctx.log.info("downloading files for for %d references", len(files))
    for f in files:
        if path_names == 'URL':
            path = remove_non_path_from_url(f.url)
            if url_prefix and path.startswith(url_prefix):
                path = path[len(url_prefix):]
            subdir, _, basename = path.rpartition('/')
        else:
            subdir = f.fileGrp
            basename = '%s%s' % (f.ID, MIME_TO_EXT.get(f.mimetype, '')) if f.ID else f.basename
        path = ctx.resolver.download_to_directory(ctx.directory, f.url, subdir=subdir, basename=basename)
        if reference != 'no-change':
            # todo: as soon as OcrdFile provides a mechanism to manage multiple FLocats, use that instead
            newref = ET.Element(TAG_METS_FLOCAT)
            newref.set('LOCTYPE', 'OTHER')
            newref.set('OTHERLOCTYPE', 'FILE')
            newref.set("{%s}href" % NS["xlink"], path)
            oldref = f._el.find('mets:FLocat', NS)
            if reference == 'replace-by-local':
                f._el.replace(oldref, newref)
            elif reference == 'insert-local':
                f._el.insert(0, newref)
            elif reference == 'append-local':
                oldref.addnext(newref)
    if reference != 'no-change':
        workspace.save_mets()

@cli.command('remove-files')
@click.option('-G', '--file-grp', help="fileGrp to add to", required=True, metavar='FILE_GRP')
@click.option('-m', '--mimetype', help="Media type of the file. Guessed from extension if not provided", required=False, metavar='TYPE')
@click.option('-g', '--page-id', help="ID of the physical page (or empty if document-global)", metavar='PAGE_ID')
@pass_workspace
def remove_files_cli(ctx, file_grp, mimetype, page_id):
    """
    remove all file references for a specific fileGrp / MIME type / page ID combination
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    files = list(workspace.find_files(file_grp=file_grp, page_id=page_id, mimetype=mimetype))
    ctx.log.info("removing references for %d files", len(files))
    for file_ in files:
        workspace.remove_file(file_.ID, keep_file=True)
    workspace.save_mets()

@cli.command('remove-file')
@click.option('-u', '--url-prefix', help="URL prefix to add to path before removing references (or else search verbatim file refs)", required=False)
@click.argument('path', type=click.Path(exists=True, dir_okay=False))
@pass_workspace
def remove_file_cli(ctx, url_prefix, path):
    """
    remove all file references for a specific location, optionally as URL
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    path = str(Path(path).absolute().relative_to(Path(ctx.directory)))
    if url_prefix:
        if not url_prefix.endswith('/'):
            url_prefix += '/'
        path = url_prefix + path
    files = list(workspace.find_files(url=path))
    ctx.log.info("removing references for %d files", len(files))
    for file_ in files:
        workspace.remove_file(file_.ID, keep_file=True)
    workspace.save_mets()

@cli.command('add-file')
@click.option('-G', '--file-grp', help="fileGrp to add to", required=True, metavar='FILE_GRP')
@click.option('-m', '--mimetype', help="Media type of the file. Guessed from extension if not provided", required=False, metavar='TYPE')
@click.option('-g', '--page-id', help="ID of the physical page (or empty if document-global)", metavar='PAGE_ID')
@click.option('-u', '--url-prefix', help="URL prefix to add to path before storing references (or else keep local file refs)", required=False)
@click.argument('path', type=click.Path(exists=True, dir_okay=False))
@pass_workspace
def add_file_cli(ctx, file_grp, mimetype, page_id, url_prefix, path):
    """
    add a file reference, optionally as URL
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    ctx.log.info("mets_target=%s", workspace.mets_target)
    assert page_id in workspace.mets.physical_pages
    page_nr = 1 + workspace.mets.physical_pages.index(page_id)
    file_id = 'FILE_' + '%04d' % page_nr + '_' + file_grp
    path = str(Path(path).absolute().relative_to(Path(ctx.directory)))
    if url_prefix:
        if not url_prefix.endswith('/'):
            url_prefix += '/'
        path = url_prefix + path
    workspace.add_file(file_grp, file_id=file_id, mimetype=mimetype, page_id=page_id, url=path, loctype='URL' if url_prefix else 'OTHER')
    workspace.save_mets()

@cli.command('add-agent')
@click.option('-m', '--mets', help="copy metsHdr/agent from this file, too", default=None)
@pass_workspace
def add_agent_cli(ctx, mets):
    """
    add agent headers, optionally from external METS
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    if mets:
        mets = OcrdMets(filename=mets)
        agents = mets.agents
    else:
        agents = []
    agents.append(OcrdAgent(_type="OTHER", othertype="SOFTWARE", role="OTHER", otherrole="publication",
                            name="ocrd/core v%s" % VERSION))
    el_metsHdr = workspace.mets._tree.getroot().find('./mets:metsHdr', NS)
    if el_metsHdr is None:
        el_metsHdr = ET.Element(TAG_METS_METSHDR)
        el_metsHdr.set('CREATEDATE', datetime.now().isoformat())
        workspace.mets._tree.getroot().insert(0, el_metsHdr)
    el_agent = None
    for agent in agents:
        if el_agent is None:
            try:
                el_agent = next(el_metsHdr.iterchildren(tag=TAG_METS_AGENT, reversed=True))
                el_agent.addnext(agent._el)
            except StopIteration:
                el_metsHdr.insert(0, agent._el)
        else:
            el_agent.addnext(agent._el)
        el_agent = agent._el
    workspace.save_mets()

@cli.command('validate')
@click.option('-u', '--url-prefix', help="validate each file has this URL prefix", required=False)
@pass_workspace
def validate_cli(ctx, url_prefix):
    """
    custom OcrdWorkspaceValidator
    """
    workspace = Workspace(ctx.resolver, ctx.directory, mets_basename=ctx.mets_basename, automatic_backup=ctx.automatic_backup)
    skip = [
        'imagefilename', # we are not primarily interested in PAGE-XML
        'dimension', # we don't modify images
        'mets_unique_identifier', # mods:identifier is optional according to DFG profile
        'mets_file_group_names', # OCR-D specific
        # we do want to validate file refs: 'mets_files',
        # we do want to enforce correct URL scheme for mets_files checks: 'url',
        # would be nice to have, too: 'non_local',
        'pixel_density', # we don't modify images
        'page', # we are not primarily interested in PAGE-XML
        # if PAGE-XML then schema-valid: 'page_xsd',
        # we do want to enforce schema validity: 'mets_xsd',
    ]
    report = WorkspaceValidator.validate(ctx.resolver, ctx.mets_url,
                                         src_dir=ctx.directory,
                                         download=False,
                                         skip=skip,
                                         page_strictness='off',
                                         page_coordinate_consistency='off')
    if url_prefix:
        for f in workspace.find_files():
            if not f.url.startswith(url_prefix):
                report.add_error("File '%s' mets:FLocat/@href has different URL prefix" % f.ID)
    if report.is_valid:
        ctx.log.info(report.to_xml())
    else:
        ctx.log.error(report.to_xml())
        sys.exit(128)
    # unfortunately, lxml (and libxml2) does not support Schematron for XSLT 2.0:
    # dfgsch = OcrdXmlDocument(filename='ddb_validierung_mets-mods-ap-digitalisierte-medien.sch')._tree
    # dfgschtrn = Schematron(dfgsch,
    #                        error_finder=Schematron.ASSERTS_AND_REPORTS, # ASSERTS_ONLY
    #                        store_report=True)
    # valid = dfgschtrn.validate(workspace.mets._tree)
    # if valid:
    #     ctx.log.info(dfgschtrn.validation_report)
    # else:
    #     ctx.log.error(dfgschtrn.validation_report)
    #     sys.exit(128)
    # TODO: validate ALTO files in FULLTEXT fileGrp syntactically (some XSD version) and semantically (coordinate plausibility, text content, ...)

