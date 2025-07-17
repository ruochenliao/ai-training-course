import { create } from 'zustand';
import { Document, DocumentList } from '@/types';

interface DocumentState {
  documents: DocumentList[];
  currentDocument: Document | null;
  isLoading: boolean;
  searchQuery: string;
  setDocuments: (documents: DocumentList[]) => void;
  setCurrentDocument: (document: Document | null) => void;
  setLoading: (loading: boolean) => void;
  setSearchQuery: (query: string) => void;
  addDocument: (document: DocumentList) => void;
  updateDocument: (id: number, updates: Partial<DocumentList>) => void;
  removeDocument: (id: number) => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  currentDocument: null,
  isLoading: false,
  searchQuery: '',

  setDocuments: (documents) => set({ documents }),

  setCurrentDocument: (document) => set({ currentDocument: document }),

  setLoading: (loading) => set({ isLoading: loading }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  addDocument: (document) => {
    const { documents } = get();
    set({ documents: [document, ...documents] });
  },

  updateDocument: (id, updates) => {
    const { documents, currentDocument } = get();
    
    // 更新文档列表
    const updatedDocuments = documents.map(doc => 
      doc.id === id ? { ...doc, ...updates } : doc
    );
    set({ documents: updatedDocuments });

    // 如果当前文档被更新，也更新当前文档
    if (currentDocument && currentDocument.id === id) {
      set({ currentDocument: { ...currentDocument, ...updates } });
    }
  },

  removeDocument: (id) => {
    const { documents } = get();
    const filteredDocuments = documents.filter(doc => doc.id !== id);
    set({ documents: filteredDocuments });

    // 如果删除的是当前文档，清空当前文档
    const { currentDocument } = get();
    if (currentDocument && currentDocument.id === id) {
      set({ currentDocument: null });
    }
  },
}));
