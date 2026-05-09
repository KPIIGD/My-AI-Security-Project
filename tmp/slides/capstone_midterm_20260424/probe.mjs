const { FileBlob, PresentationFile } = await import('@oai/artifact-tool');
console.log('ok', typeof FileBlob.load, typeof PresentationFile.importPptx);
