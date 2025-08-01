'use client';
import { FileUp } from 'lucide-react';
import React, { useState, useRef } from 'react';

import { Spinner } from '@/components/Spinner';
import { Button } from '@/components/ui/Button';
import { useUserContext } from '@/context/UserContext';
import { UpdateButtonContainerProps } from '@/types';

const UpdateButtonContainer: React.FC<UpdateButtonContainerProps> = ({
  id,
  onUpdateSuccess,
  showToast,
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { getClient } = useUserContext();

  const handleDocumentUpdate = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    event.preventDefault();
    if (
      fileInputRef.current &&
      fileInputRef.current.files &&
      fileInputRef.current.files.length
    ) {
      setIsUpdating(true);
      const file = fileInputRef.current.files[0];

      try {
        const client = await getClient();
        if (!client) {
          throw new Error('Failed to get authenticated client');
        }

        const metadata = { title: file.name };

        await client.documents.create({
          id: id,
          file: file,
          metadata: [metadata],
        });

        showToast({
          variant: 'success',
          title: '上传成功',
          description: '所有文件已成功上传。',
        });
        onUpdateSuccess();
      } catch (error: any) {
        console.error('Error updating file:', error);
        console.error('Error details:', error.response?.data);
        showToast({
          variant: 'destructive',
          title: '上传失败',
          description: error.message || '发生了未知错误',
        });
      } finally {
        setIsUpdating(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  const handleUpdateButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div>
      <Button
        onClick={handleUpdateButtonClick}
        disabled={isUpdating}
        color={isUpdating ? 'disabled' : 'filled'}
        shape="slim"
        tooltip="Update Document"
      >
        {isUpdating ? (
          <Spinner className="h-6 w-6 text-white" />
        ) : (
          <FileUp className="h-6 w-6" />
        )}
      </Button>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleDocumentUpdate}
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default UpdateButtonContainer;
