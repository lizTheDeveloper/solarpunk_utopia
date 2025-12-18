import { useState } from 'react';
import { useFileManifests, useUploadFile, useFileStats } from '@/hooks/useFiles';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FileText, Upload, Download, FolderOpen, Tag } from 'lucide-react';
import { formatBytes, formatTimeAgo } from '@/utils/formatters';

export function KnowledgePage() {
  const { data: files, isLoading: filesLoading, error } = useFileManifests();
  const { data: fileStats } = useFileStats();
  const uploadFile = useUploadFile();

  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('education');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadError, setUploadError] = useState('');

  const filteredFiles = files?.filter(
    (file) => selectedCategory === 'all' || file.category === selectedCategory
  ) || [];

  const categories = ['education', 'protocols', 'guides', 'lessons', 'documentation'];

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadingFile(file);
      setUploadError('');
    }
  };

  const handleUpload = async () => {
    if (!uploadingFile) return;

    try {
      await uploadFile.mutateAsync({
        file: uploadingFile,
        metadata: {
          category: uploadCategory,
          description: uploadDescription || undefined,
        },
      });
      setUploadingFile(null);
      setUploadDescription('');
    } catch (error) {
      setUploadError('Failed to upload file. Please try again.');
    }
  };

  const handleDownload = async (fileId: string, filename: string) => {
    // Trigger download
    const link = document.createElement('a');
    link.href = `/api/files/download/${fileId}`;
    link.download = filename;
    link.click();
  };

  if (error) {
    return <ErrorMessage message="Failed to load files. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Library</h1>
        <p className="text-gray-600 mt-1">
          Share and access community knowledge, guides, and resources
        </p>
      </div>

      {/* Stats */}
      {fileStats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-solarpunk-600" />
              <div>
                <p className="text-sm text-gray-600">Total Files</p>
                <p className="text-2xl font-bold text-gray-900">{fileStats.total_files}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <FolderOpen className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Total Chunks</p>
                <p className="text-2xl font-bold text-gray-900">{fileStats.total_chunks}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <Upload className="w-8 h-8 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600">Total Storage</p>
                <p className="text-2xl font-bold text-gray-900">{formatBytes(fileStats.total_bytes)}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Upload Section */}
      <Card>
        <h3 className="font-semibold text-gray-900 mb-4">Upload a File</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File
            </label>
            <input
              type="file"
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
            {uploadingFile && (
              <p className="text-sm text-gray-600 mt-2">
                Selected: {uploadingFile.name} ({formatBytes(uploadingFile.size)})
              </p>
            )}
          </div>

          {uploadingFile && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                  placeholder="Brief description of this file..."
                />
              </div>

              {uploadError && <ErrorMessage message={uploadError} />}

              <Button
                onClick={handleUpload}
                disabled={uploadFile.isPending}
                fullWidth
              >
                {uploadFile.isPending ? 'Uploading...' : 'Upload File'}
              </Button>
            </>
          )}
        </div>
      </Card>

      {/* Filter */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Category:</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Files List */}
      {filesLoading ? (
        <Loading text="Loading files..." />
      ) : filteredFiles.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Showing {filteredFiles.length} file{filteredFiles.length !== 1 ? 's' : ''}
          </p>
          {filteredFiles.map((file) => (
            <Card key={file.id} hoverable>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <FileText className="w-8 h-8 text-solarpunk-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900">{file.filename}</h3>
                    {file.description && (
                      <p className="text-sm text-gray-600 mt-1">{file.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Tag className="w-4 h-4" />
                        <span>{file.category || 'Uncategorized'}</span>
                      </div>
                      <span>{formatBytes(file.total_size)}</span>
                      <span>{file.total_chunks} chunks</span>
                    </div>
                    {file.keywords && file.keywords.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap mt-2">
                        {file.keywords.map((keyword, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-solarpunk-50 text-solarpunk-700 rounded text-xs"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      Uploaded {formatTimeAgo(file.created_at)}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleDownload(file.id, file.filename)}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 mb-2">
              {selectedCategory !== 'all'
                ? `No files in ${selectedCategory} category.`
                : 'No files uploaded yet.'}
            </p>
            <p className="text-sm text-gray-500">
              Upload guides, protocols, and educational materials to share with the community
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
