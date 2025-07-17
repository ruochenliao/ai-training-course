import { motion, AnimatePresence } from 'framer-motion';

interface ToastProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
}

export const Toast = ({ message, isVisible, onClose }: ToastProps) => {
  if (!isVisible) return null;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50"
          onAnimationComplete={() => {
            setTimeout(onClose, 2000);
          }}
        >
          <div className="bg-gray-800 text-white px-4 py-2 rounded-full text-sm shadow-lg">
            {message}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};