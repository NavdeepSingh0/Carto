import React from 'react';
import { User, Wallet, Leaf, Flame } from 'lucide-react';

const profiles = [
    { id: 'budget', name: 'Budget Explorer', icon: Wallet },
    { id: 'premium', name: 'Premium Diner', icon: Flame },
    { id: 'health', name: 'Health Conscious', icon: Leaf },
];

export default function ProfileSelector({ selected, onSelect }) {
    return (
        <div className="flex flex-col h-full justify-center">
            <div className="flex items-center gap-2 mb-4">
                <User size={20} className="text-zomato-red" />
                <h2 className="font-bold text-lg text-zomato-charcoal">Select Persona</h2>
            </div>

            <div className="flex overflow-x-auto gap-3 pb-2 hide-scrollbar snap-x">
                {profiles.map(p => {
                    const Icon = p.icon;
                    const isActive = selected?.id === p.id;
                    return (
                        <button
                            key={p.id}
                            onClick={() => onSelect(p)}
                            className={`snap-start flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap font-medium transition-colors border-2 ${isActive
                                    ? 'bg-zomato-red text-white border-zomato-red'
                                    : 'bg-zomato-lightgray text-zomato-charcoal border-transparent hover:border-zomato-red/20'
                                }`}
                        >
                            <Icon size={16} />
                            {p.name}
                        </button>
                    )
                })}
            </div>
        </div>
    );
}
