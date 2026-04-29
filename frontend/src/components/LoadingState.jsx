export default function LoadingState({ withRationale }) {
  return (
    <div className="mt-8 space-y-3">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
          <div className="flex gap-4">
            <div className="w-6 h-6 rounded-full bg-gray-100 shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="flex gap-2">
                <div className="h-4 w-28 bg-gray-100 rounded" />
                <div className="h-4 w-20 bg-gray-100 rounded" />
                <div className="h-4 w-32 bg-gray-100 rounded" />
              </div>
              <div className="h-4 w-3/4 bg-gray-100 rounded" />
            </div>
          </div>
        </div>
      ))}
      <p className="text-center text-sm text-gray-400 mt-4">
        {withRationale
          ? 'Finding standards and generating explanations...'
          : 'Finding applicable BIS standards...'
        }
      </p>
    </div>
  )
}