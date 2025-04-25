import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Image from 'next/image';
import Head from 'next/head';

interface User {
  username: string;
  displayName: string;
  bio: string;
  followers: number;
  following: number;
  likes: number;
  verified: boolean;
  profileImage: string;
  videosCount: number;
}

interface Video {
  id: string;
  caption: string;
  coverImage: string;
  plays: number;
  likes: number;
  comments: number;
  shares: number;
  videoUrl: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const { username } = router.query;
  const [user, setUser] = useState<User | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!username) return;

    const fetchUserProfile = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/${username}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }
        
        const data = await response.json();
        setUser(data.user);
        setVideos(data.videos);
      } catch (err) {
        console.error('Error fetching profile:', err);
        setError('Could not load profile. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, [username]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 p-4 rounded-md text-red-800">
          {error || 'User not found'}
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>{user.displayName} (@{user.username}) | TikTok Analyzer</title>
        <meta name="description" content={`${user.displayName} TikTok profile - ${user.bio}`} />
      </Head>
      
      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Profile Header */}
          <div className="p-6 border-b">
            <div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
              <div className="relative h-24 w-24 rounded-full overflow-hidden bg-gray-200">
                {user.profileImage ? (
                  <Image 
                    src={user.profileImage} 
                    alt={user.displayName} 
                    fill
                    className="object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center bg-gray-300 text-gray-500">
                    <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-4c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z" />
                    </svg>
                  </div>
                )}
              </div>

              <div className="flex-1 text-center sm:text-left">
                <div className="flex flex-col sm:flex-row sm:items-center">
                  <h1 className="text-2xl font-bold">{user.displayName}</h1>
                  <span className="text-lg text-gray-600 mt-1 sm:mt-0 sm:ml-2">@{user.username}</span>
                  {user.verified && (
                    <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded-full">Verified</span>
                  )}
                </div>
                
                <p className="text-gray-600 mt-2">{user.bio}</p>
                
                <div className="flex justify-center sm:justify-start mt-4 space-x-6">
                  <div className="text-center">
                    <span className="block font-bold">{user.videosCount.toLocaleString()}</span>
                    <span className="text-sm text-gray-500">Videos</span>
                  </div>
                  <div className="text-center">
                    <span className="block font-bold">{user.followers.toLocaleString()}</span>
                    <span className="text-sm text-gray-500">Followers</span>
                  </div>
                  <div className="text-center">
                    <span className="block font-bold">{user.following.toLocaleString()}</span>
                    <span className="text-sm text-gray-500">Following</span>
                  </div>
                  <div className="text-center">
                    <span className="block font-bold">{user.likes.toLocaleString()}</span>
                    <span className="text-sm text-gray-500">Likes</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Videos Grid */}
          <div className="p-6">
            <h2 className="text-xl font-bold mb-4">Videos</h2>
            
            {videos.length === 0 ? (
              <p className="text-gray-600">No videos found for this user.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {videos.map((video) => (
                  <div key={video.id} className="bg-gray-50 rounded-md overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                    <div className="relative h-48 w-full bg-gray-200">
                      <Image 
                        src={video.coverImage} 
                        alt={video.caption}
                        fill
                        className="object-cover"
                      />
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-1 py-0.5 rounded">
                        {video.plays.toLocaleString()} views
                      </div>
                    </div>
                    
                    <div className="p-3">
                      <p className="text-sm line-clamp-2">{video.caption}</p>
                      
                      <div className="flex justify-between mt-2 text-xs text-gray-500">
                        <span>{video.likes.toLocaleString()} likes</span>
                        <span>{video.comments.toLocaleString()} comments</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
} 