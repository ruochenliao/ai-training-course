import React from 'react';

import { useToast } from '@/components/ui/use-toast';

interface CopyableContentProps {
  content: string;
  truncated: string;
}

const CopyableContent: React.FC<CopyableContentProps> = ({
  content,
  truncated,
}) => {
  const { toast } = useToast();

  const handleCopy = () => {
    navigator.clipboard
      .writeText(content)
      .then(() => toast({ title: '已复制!' }))
      .catch((err) => console.error('Could not copy text: ', err));
  };

  return (
    <div
      className="cursor-pointer"
      onClick={handleCopy}
      title={`点击复制: ${content}`}
    >
      {truncated}
    </div>
  );
};

export default CopyableContent;
