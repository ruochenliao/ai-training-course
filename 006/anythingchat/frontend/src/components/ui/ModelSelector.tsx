import React, { useState, useEffect } from 'react';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useUserContext } from '@/context/UserContext';
import { ModelSelectorProps } from '@/types';

import { Button } from './Button';

const predefinedModels = [
  { value: 'gpt-4o-mini', label: 'gpt-4o-mini' },
  { value: 'gpt-4o', label: 'gpt-4o' },
  { value: 'ollama/llama3.1', label: 'ollama/llama3.1' },
];

const ModelSelector: React.FC<ModelSelectorProps> = ({ id }) => {
  const { selectedModel, setSelectedModel } = useUserContext();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [customModelValue, setCustomModelValue] = useState<string | null>('');
  const [allModels, setAllModels] = useState(predefinedModels);

  useEffect(() => {}, [selectedModel, allModels]);

  const handleSelectChange = (value: string) => {
    if (value === 'add_custom') {
      setIsDialogOpen(true);
    } else {
      setSelectedModel(value);
    }
  };

  const handleCustomModelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomModelValue(e.target.value || null);
  };

  const handleCustomModelSubmit = () => {
    if (customModelValue !== null && customModelValue.trim() !== '') {
      const trimmedValue = customModelValue.trim();
      const newModel = { value: trimmedValue, label: trimmedValue };
      setAllModels((prevModels) => [...prevModels, newModel]);
      setSelectedModel(trimmedValue);
      setCustomModelValue(null);
      setIsDialogOpen(false);
    } else {
      console.warn('Attempted to submit empty custom model name');
    }
  };

  return (
    <div id={id}>
      <Select value={selectedModel} onValueChange={handleSelectChange}>
        <SelectTrigger>
          <SelectValue placeholder="选择模型" />
        </SelectTrigger>
        <SelectContent>
          {allModels.map((model) => (
            <SelectItem key={model.value} value={model.value}>
              {model.label}
            </SelectItem>
          ))}
          <SelectItem value="add_custom">添加其他模型</SelectItem>
        </SelectContent>
      </Select>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加新模型</DialogTitle>
            <DialogDescription>
              输入您希望使用的模型名称。
            </DialogDescription>
          </DialogHeader>
          <div>
            <input
              type="text"
              value={customModelValue ?? ''}
              onChange={handleCustomModelChange}
              className="mt-2 block w-full py-2 px-3 border border-gray-300 bg-white rounded-2xl shadow-sm focus:outline-none focus:ring-accent-dark focus:border-accent-dark sm:text-sm text-black"
              placeholder="输入自定义模型名称"
            />
            <Button
              onClick={handleCustomModelSubmit}
              color="primary"
              className="mt-4 inline-flex justify-center py-2 px-4 "
            >
              提交
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ModelSelector;
