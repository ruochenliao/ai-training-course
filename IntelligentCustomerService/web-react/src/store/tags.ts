import {create} from 'zustand'
import {persist} from 'zustand/middleware'

export interface TagItem {
  path: string
  title: string
  name: string
  icon?: string
  closable?: boolean
}

interface TagsState {
  tags: TagItem[]
  activeTag: string
  addTag: (tag: TagItem) => void
  removeTag: (path: string) => void
  removeOtherTags: (path: string) => void
  removeLeftTags: (path: string) => void
  removeRightTags: (path: string) => void
  removeAllTags: () => void
  setActiveTag: (path: string) => void
  updateTag: (path: string, updates: Partial<TagItem>) => void
}

export const useTagsStore = create<TagsState>()(
  persist(
    (set, get) => ({
      tags: [
        {
          path: '/workbench',
          title: '工作台',
          name: 'Workbench',
          icon: 'mdi:view-dashboard',
          closable: false,
        },
      ],
      activeTag: '/workbench',

      addTag: (tag: TagItem) => {
        const { tags } = get()
        const existingTag = tags.find((t) => t.path === tag.path)

        if (!existingTag) {
          set({
            tags: [...tags, { ...tag, closable: tag.closable ?? true }],
            activeTag: tag.path,
          })
        } else {
          set({ activeTag: tag.path })
        }
      },

      removeTag: (path: string) => {
        const { tags, activeTag } = get()
        const newTags = tags.filter((tag) => tag.path !== path)

        let newActiveTag = activeTag
        if (activeTag === path && newTags.length > 0) {
          // 如果删除的是当前激活的标签，激活最后一个标签
          newActiveTag = newTags[newTags.length - 1].path
        }

        set({ tags: newTags, activeTag: newActiveTag })
      },

      removeOtherTags: (path: string) => {
        const { tags } = get()
        const currentTag = tags.find((tag) => tag.path === path)
        const homeTag = tags.find((tag) => tag.path === '/workbench')

        const newTags = [homeTag, currentTag].filter(Boolean) as TagItem[]
        set({ tags: newTags, activeTag: path })
      },

      removeLeftTags: (path: string) => {
        const { tags } = get()
        const currentIndex = tags.findIndex((tag) => tag.path === path)
        if (currentIndex > 0) {
          const newTags = tags.slice(currentIndex)
          set({ tags: newTags })
        }
      },

      removeRightTags: (path: string) => {
        const { tags } = get()
        const currentIndex = tags.findIndex((tag) => tag.path === path)
        if (currentIndex >= 0 && currentIndex < tags.length - 1) {
          const newTags = tags.slice(0, currentIndex + 1)
          set({ tags: newTags })
        }
      },

      removeAllTags: () => {
        const homeTag = {
          path: '/workbench',
          title: '工作台',
          name: 'Workbench',
          icon: 'mdi:view-dashboard',
          closable: false,
        }
        set({ tags: [homeTag], activeTag: '/workbench' })
      },

      setActiveTag: (path: string) => {
        set({ activeTag: path })
      },

      updateTag: (path: string, updates: Partial<TagItem>) => {
        const { tags } = get()
        const newTags = tags.map((tag) => (tag.path === path ? { ...tag, ...updates } : tag))
        set({ tags: newTags })
      },
    }),
    {
      name: 'tags-storage',
      partialize: (state) => ({
        tags: state.tags,
        activeTag: state.activeTag,
      }),
    },
  ),
)
