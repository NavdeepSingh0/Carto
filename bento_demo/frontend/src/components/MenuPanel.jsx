import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Plus, Check } from 'lucide-react';

const CATEGORY_COLORS = {
    Main: '#E23744',
    Beverage: '#34D399',
    Dessert: '#F472B6',
    Extension: '#FB923C',
    Side: '#A78BFA',
    Starter: '#38BDF8',
};

export default function MenuPanel({ menu, cart, onAddToCart, selectedRestaurantId }) {
    const [showMenu, setShowMenu] = useState(false);

    // Automatically show menu when items are available
    React.useEffect(() => {
        if (menu.length > 0) setShowMenu(true);
        else setShowMenu(false);
    }, [menu, selectedRestaurantId]);

    return (
        <div className="rounded-[24px] overflow-hidden relative" style={{ height: '100%', background: '#000' }}>
            <AnimatePresence mode="wait">
                {!showMenu ? (
                    /* HERO CARD — shown when no restaurant or menu */
                    <motion.div
                        key="hero"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="w-full h-full relative group"
                    >
                        <div className="w-full h-full" style={{
                            background: 'linear-gradient(135deg, #1A1A1A 0%, #2D1810 50%, #1A1A1A 100%)',
                        }}>
                            <div className="absolute inset-0 flex items-center justify-center opacity-20">
                                <div className="text-[120px]">🍲</div>
                            </div>
                        </div>

                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <button className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-md border border-white/30 flex items-center justify-center text-white shadow-xl hover:scale-110 transition-transform duration-300">
                                <Play size={28} fill="white" />
                            </button>
                        </div>

                        <div className="absolute bottom-0 left-0 right-0 p-5 bg-gradient-to-t from-black via-black/70 to-transparent">
                            <h3 className="text-white font-bold text-base leading-tight">Perfect Samosa</h3>
                            <p className="text-gray-300 text-[10px] mt-1 line-clamp-2">Watch our chefs prepare this delicacy fresh in our kitchen.</p>
                        </div>

                        <div className="absolute top-4 right-4 text-white text-[9px] font-bold px-2 py-1 rounded-md animate-pulse flex items-center gap-1 shadow-lg"
                            style={{ background: '#E23744', boxShadow: '0 4px 14px rgba(226,55,68,0.5)' }}>
                            <span className="w-1.5 h-1.5 rounded-full bg-white"></span> LIVE
                        </div>
                    </motion.div>
                ) : (
                    /* MENU LIST — shown when restaurant is selected */
                    <motion.div
                        key="menu"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="w-full h-full flex flex-col bg-white"
                    >
                        {/* Header */}
                        <div className="px-5 py-4 border-b border-gray-100 bg-white/90 backdrop-blur-md z-10 sticky top-0">
                            <div className="flex items-center justify-between">
                                <h3 className="section-label flex items-center gap-2">
                                    <span style={{ color: '#E23744' }}>🍽️</span> Menu Items
                                </h3>
                                <span className="text-[10px] text-gray-400 font-medium">{menu.length} items</span>
                            </div>
                        </div>

                        {/* Scrollable items */}
                        <div className="flex-grow overflow-y-auto custom-scroll">
                            {menu.map((item, idx) => {
                                const inCart = cart.some(c => c.item_id === item.item_id);
                                const catColor = CATEGORY_COLORS[item.category] || '#6B7280';

                                return (
                                    <motion.div
                                        key={item.item_id}
                                        initial={{ opacity: 0, y: 6 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.02 }}
                                        className="flex items-center justify-between px-5 py-3 border-b border-gray-50 hover:bg-gray-50/80 transition-colors group"
                                    >
                                        <div className="flex items-center gap-3 min-w-0">
                                            {/* Veg/Non-veg dot */}
                                            <span className={`w-3 h-3 border p-[1px] flex items-center justify-center rounded-[2px] flex-shrink-0 ${item.is_veg ? 'border-green-600' : 'border-red-500'
                                                }`}>
                                                <span className={`w-1.5 h-1.5 rounded-full ${item.is_veg ? 'bg-green-600' : 'bg-red-500'}`}></span>
                                            </span>

                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-semibold truncate" style={{ color: 'var(--color-zomato-charcoal)' }}>
                                                        {item.item_name}
                                                    </span>
                                                    <span
                                                        className="text-[9px] font-bold px-1.5 py-0.5 rounded-md flex-shrink-0"
                                                        style={{ background: catColor + '15', color: catColor }}
                                                    >
                                                        {item.category}
                                                    </span>
                                                </div>
                                                <span className="text-[11px] font-mono text-gray-500">₹{item.price}</span>
                                            </div>
                                        </div>

                                        {/* Add button */}
                                        {inCart ? (
                                            <div className="flex items-center gap-1 text-[10px] font-semibold text-green-600 flex-shrink-0">
                                                <Check size={12} /> Added
                                            </div>
                                        ) : (
                                            <motion.button
                                                whileHover={{ scale: 1.1 }}
                                                whileTap={{ scale: 0.9 }}
                                                onClick={() => onAddToCart(item)}
                                                className="w-7 h-7 rounded-full bg-gray-50 flex items-center justify-center hover:bg-[#E23744] hover:text-white transition-colors flex-shrink-0 cursor-pointer"
                                                style={{ color: '#E23744' }}
                                            >
                                                <Plus size={14} />
                                            </motion.button>
                                        )}
                                    </motion.div>
                                );
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
