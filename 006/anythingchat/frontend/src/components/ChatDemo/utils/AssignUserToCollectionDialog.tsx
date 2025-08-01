import { Loader } from 'lucide-react';
import { User } from 'r2r-js';
import React, { useState, useEffect, useCallback } from 'react';

import Table, { Column } from '@/components/ChatDemo/Table';
import { Button } from '@/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { useUserContext } from '@/context/UserContext';

interface AssignUserToCollectionDialogProps {
  open: boolean;
  onClose: () => void;
  collection_id: string;
  onAssignSuccess: () => void;
}

const AssignUserToCollectionDialog: React.FC<
  AssignUserToCollectionDialogProps
> = ({ open, onClose, collection_id, onAssignSuccess }) => {
  const { getClient } = useUserContext();
  const { toast } = useToast();

  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [assigning, setAssigning] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAllUsers = useCallback(async () => {
    setLoading(true);
    try {
      const client = await getClient();
      if (!client) {
        throw new Error('Failed to get authenticated client');
      }

      const data = await client.users.list();
      const usersWithId = data.results.map((user: User) => ({
        ...user,
        id: user.id,
      }));

      // Filter usersWithId directly
      const filteredUsers = usersWithId.filter(
        (filteredUser) => !filteredUser.collectionIds.includes(collection_id)
      );

      setAllUsers(usersWithId);
      setFilteredUsers(filteredUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast({
        title: '错误',
        description: '获取用户失败，请稍后重试。',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [getClient, toast]);

  useEffect(() => {
    if (open) {
      fetchAllUsers();
      setSelectedUserIds([]);
      setSearchQuery('');
    }
  }, [open, fetchAllUsers]);

  useEffect(() => {
    const usersNotInCollection = allUsers.filter(
      (user) => !user.collectionIds.includes(collection_id)
    );

    if (searchQuery.trim() === '') {
      setFilteredUsers(usersNotInCollection);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = usersNotInCollection.filter(
        (user) =>
          user.id.toLowerCase().includes(query) ||
          (user.name && user.name.toLowerCase().includes(query)) ||
          (user.email && user.email.toLowerCase().includes(query))
      );
      setFilteredUsers(filtered);
    }
  }, [searchQuery, allUsers, collection_id]);

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedUserIds(filteredUsers.map((user) => user.id));
    } else {
      setSelectedUserIds([]);
    }
  };

  const handleSelectItem = (id: string, selected: boolean) => {
    setSelectedUserIds((prev) => {
      if (selected) {
        return [...prev, id];
      } else {
        return prev.filter((userId) => userId !== id);
      }
    });
  };

  const handleAssign = async () => {
    if (selectedUserIds.length === 0) {
      toast({
        title: '未选择用户',
        description: '请至少选择一个用户进行分配。',
        variant: 'destructive',
      });
      return;
    }

    setAssigning(true);
    try {
      const client = await getClient();
      if (!client) {
        throw new Error('Failed to get authenticated client');
      }

      const assignPromises = selectedUserIds.map((id) =>
        client.collections.addUser({
          id: collection_id,
          userId: id,
        })
      );

      await Promise.all(assignPromises);

      toast({
        title: '成功',
        description: '选中的用户已分配到集合。',
        variant: 'success',
      });

      onAssignSuccess();
      onClose();
    } catch (error) {
      console.error('Error assigning users:', error);
      toast({
        title: '错误',
        description: '分配用户失败，请稍后重试。',
        variant: 'destructive',
      });
    } finally {
      setAssigning(false);
    }
  };

  const columns: Column<User>[] = [
    { key: 'id', label: '用户ID', truncate: true, copyable: true },
    { key: 'email', label: '邮箱' },
    { key: 'name', label: '姓名' },
  ];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="text-white max-w-4xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold mb-4">
            分配用户到集合
          </DialogTitle>
          <Input
            placeholder="按用户ID、姓名或邮箱搜索"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="mb-4"
          />
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center items-center mt-20">
            <Loader className="animate-spin" size={64} />
          </div>
        ) : (
          <Table<User>
            data={filteredUsers}
            columns={columns}
            itemsPerPage={filteredUsers.length}
            onSelectAll={handleSelectAll}
            onSelectItem={handleSelectItem}
            selectedItems={selectedUserIds}
            initialSort={{ key: 'userId', order: 'asc' }}
            initialFilters={{}}
            tableHeight="400px"
            currentPage={1}
            onPageChange={() => {}}
            showPagination={false}
            loading={loading}
          />
        )}
        <DialogFooter className="mt-4 flex justify-end space-x-2">
          <Button
            onClick={handleAssign}
            color="filled"
            disabled={assigning || selectedUserIds.length === 0}
            style={{ zIndex: 20 }}
          >
            分配到集合
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AssignUserToCollectionDialog;
