import React, { useEffect, useState, useRef } from 'react';
import { X, Loader2, Download, AlertCircle } from 'lucide-react';
import * as docx from 'docx-preview';
import * as XLSX from 'xlsx';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const FilePreview = ({ file, onClose, apiUrl, apiKey }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [content, setContent] = useState(null); // For custom rendered content (HTML/MD)
    const [blobUrl, setBlobUrl] = useState(null);
    const containerRef = useRef(null);

    const fileExt = file?.source ? file.source.split('.').pop().toLowerCase() : '';
    const isPdf = fileExt === 'pdf';
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExt);
    const isDocx = fileExt === 'docx';
    const isExcel = ['xlsx', 'xls', 'csv'].includes(fileExt);
    const isMarkdown = ['md', 'txt', 'log'].includes(fileExt);

    useEffect(() => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setContent(null); // Reset content

        const fetchFile = async () => {
            try {
                const response = await axios.get(`${apiUrl}/files`, {
                    params: { path: file.source },
                    headers: { 'Authorization': `Bearer ${apiKey}` },
                    responseType: 'blob'
                });

                const blob = response.data;
                const url = URL.createObjectURL(blob);
                setBlobUrl(url); // Store for cleanup

                if (isDocx) {
                    if (containerRef.current) {
                        await docx.renderAsync(blob, containerRef.current);
                    }
                } else if (isExcel) {
                    const buffer = await blob.arrayBuffer();
                    const workbook = XLSX.read(buffer, { type: 'array' });
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const html = XLSX.utils.sheet_to_html(firstSheet, {
                        header: '',
                        footer: '',
                        editable: false
                    });
                    setContent(html);
                } else if (isMarkdown) {
                    const text = await blob.text();
                    setContent(text);
                }
                // PDF and Images use the blob URL directly in iframe/img tag

                setLoading(false);
            } catch (err) {
                console.error("Preview Error:", err);
                setError("Failed to load file preview. Ensure the backend is allowed to access this path.");
                setLoading(false);
            }
        };

        fetchFile();

        return () => {
            if (blobUrl) URL.revokeObjectURL(blobUrl);
        };
    }, [file]);

    if (!file) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 md:p-8">
            <div className="bg-neutral-900 w-full h-full max-w-6xl rounded-xl border border-red-900/30 shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-red-900/20 bg-neutral-950">
                    <div className="flex items-center gap-2 overflow-hidden">
                        <span className="text-gray-200 font-medium truncate max-w-md">{file.title || file.source.split(/[\\/]/).pop()}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-900/40 text-red-300 border border-red-500/20 uppercase font-bold">{fileExt}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {blobUrl && (
                            <a href={blobUrl} download={file.source.split(/[\\/]/).pop()} className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition" title="Download">
                                <Download size={20} />
                            </a>
                        )}
                        <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-red-500/20 rounded-lg transition">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 bg-neutral-100 relative overflow-hidden flex flex-col">
                    {loading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900/20 z-10 backdrop-blur-[1px]">
                            <div className="bg-black/80 text-white px-4 py-2 rounded-lg flex items-center gap-2 shadow-lg">
                                <Loader2 className="animate-spin text-red-500" />
                                <span>Loading Preview...</span>
                            </div>
                        </div>
                    )}

                    {error ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-red-500 gap-2 bg-neutral-900">
                            <AlertCircle size={48} />
                            <p>{error}</p>
                        </div>
                    ) : (
                        <div className="w-full h-full overflow-auto bg-white text-black">
                            {isPdf ? (
                                <iframe src={blobUrl} className="w-full h-full border-none" title="PDF Preview" />
                            ) : isImage ? (
                                <div className="w-full h-full flex items-center justify-center bg-neutral-900">
                                    <img src={blobUrl} alt="Preview" className="max-w-full max-h-full object-contain" />
                                </div>
                            ) : isDocx ? (
                                <div ref={containerRef} className="docx-wrapper p-8 bg-white min-h-full shadow-sm" />
                            ) : isExcel ? (
                                <div className="p-4 overflow-auto bg-white excel-wrapper text-sm" dangerouslySetInnerHTML={{ __html: content }} />
                            ) : isMarkdown ? (
                                <div className="p-8 bg-neutral-900 text-gray-100 min-h-full overflow-auto prose prose-invert max-w-none">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            code({ node, inline, className, children, ...props }) {
                                                const match = /language-(\w+)/.exec(className || '')
                                                return !inline && match ? (
                                                    <SyntaxHighlighter
                                                        {...props}
                                                        style={vscDarkPlus}
                                                        language={match[1]}
                                                        PreTag="div"
                                                    >{String(children).replace(/\n$/, '')}</SyntaxHighlighter>
                                                ) : (
                                                    <code {...props} className={className}>
                                                        {children}
                                                    </code>
                                                )
                                            }
                                        }}
                                    >
                                        {content}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center gap-4 bg-neutral-800 text-gray-400">
                                    <div className="text-6xl">📄</div>
                                    <div className="text-center">
                                        <p className="text-lg text-gray-200 mb-1">Preview not available for <b>.{fileExt}</b> files.</p>
                                        <p className="text-sm">Please download the file to view it.</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FilePreview;
