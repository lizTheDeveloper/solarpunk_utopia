import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCells, useMyCells } from '@/hooks/useCells';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { CellCard } from '@/components/CellCard';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Plus, Users, Filter } from 'lucide-react';

export function CellsPage() {
  const navigate = useNavigate();
  const [view, setView] = useState<'all' | 'my'>('my');
  const [acceptingOnly, setAcceptingOnly] = useState(true);

  const { data: allCells, isLoading: loadingAll, error: errorAll } = useCells({
    accepting_members_only: acceptingOnly,
  });
  const { data: myCells, isLoading: loadingMy, error: errorMy } = useMyCells();

  const isLoading = view === 'all' ? loadingAll : loadingMy;
  const error = view === 'all' ? errorAll : errorMy;
  const cells = view === 'all' ? allCells : myCells;

  if (error) {
    return <ErrorMessage message="Failed to load cells. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Local Cells</h1>
          <p className="text-gray-600 mt-1">
            Connect with your local community (5-50 people who can meet IRL)
          </p>
        </div>
        <Button onClick={() => navigate('/cells/create')}>
          <Plus className="w-4 h-4 mr-2" />
          Create Cell
        </Button>
      </div>

      {/* View Tabs */}
      <Card>
        <div className="flex items-center gap-4 mb-4">
          <button
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === 'my'
                ? 'bg-solarpunk-100 text-solarpunk-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            onClick={() => setView('my')}
          >
            <Users className="w-4 h-4 inline mr-2" />
            My Cells ({myCells?.length || 0})
          </button>
          <button
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === 'all'
                ? 'bg-solarpunk-100 text-solarpunk-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            onClick={() => setView('all')}
          >
            <Filter className="w-4 h-4 inline mr-2" />
            Discover Cells
          </button>
        </div>

        {view === 'all' && (
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={acceptingOnly}
                onChange={(e) => setAcceptingOnly(e.target.checked)}
                className="rounded text-solarpunk-600 focus:ring-solarpunk-500"
              />
              Only show cells accepting new members
            </label>
          </div>
        )}
      </Card>

      {/* Cells Grid */}
      {isLoading ? (
        <Loading />
      ) : cells && cells.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cells.map((cell) => (
            <CellCard
              key={cell.id}
              cell={cell}
              onClick={() => navigate(`/cells/${cell.id}`)}
              showActions
            />
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {view === 'my' ? 'No cells yet' : 'No cells found'}
            </h3>
            <p className="text-gray-600 mb-6">
              {view === 'my'
                ? 'Join a cell to start connecting with your local community'
                : 'Try adjusting your filters or create a new cell'}
            </p>
            {view === 'my' && (
              <Button onClick={() => setView('all')}>
                Discover Cells
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
