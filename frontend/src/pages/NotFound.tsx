import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Home, ArrowLeft } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-slate-50 to-blue-50">
      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardContent className="text-center p-12 space-y-6">
          <div className="space-y-4">
            <h1 className="text-8xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              404
            </h1>
            <h2 className="text-2xl font-bold text-gray-800">Page Not Found</h2>
            <p className="text-lg text-gray-600">
              Oops! The page you're looking for doesn't exist.
            </p>
          </div>
          
          <div className="flex flex-col gap-3 pt-4">
            <Button asChild className="button w-full py-3 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-300">
              <a href="/">
                <Home className="mr-2 h-5 w-5" />
          Return to Home
        </a>
            </Button>
            <Button 
              variant="outline" 
              onClick={() => window.history.back()}
              className="w-full py-3 text-base font-semibold shadow-md hover:shadow-lg transition-all duration-300"
            >
              <ArrowLeft className="mr-2 h-5 w-5" />
              Go Back
            </Button>
      </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NotFound;
