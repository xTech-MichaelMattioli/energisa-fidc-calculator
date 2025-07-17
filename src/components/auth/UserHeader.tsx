import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../ui/dropdown-menu';
import { Badge } from '../ui/badge';
import { LogOut, User, Settings } from 'lucide-react';

export const UserHeader: React.FC = () => {
  const { user, profile, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  const getUserInitials = (name?: string, email?: string) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    if (email) {
      return email.slice(0, 2).toUpperCase();
    }
    return 'US';
  };

  if (!user || !profile) {
    return null;
  }

  return (
    <div className="flex items-center justify-between p-4 border-b bg-white">
      <div className="flex items-center space-x-3">
        <h1 className="text-xl font-bold text-gray-900">
          Energisa Data Refactor
        </h1>
        <Badge variant="secondary" className="text-xs">
          FIDC Processing
        </Badge>
      </div>
      
      <div className="flex items-center space-x-4">
        <div className="hidden md:block text-right">
          <p className="text-sm font-medium text-gray-900">
            {profile.full_name || 'Usuário'}
          </p>
          <p className="text-xs text-gray-500">
            {profile.email}
          </p>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src={profile.avatar_url} alt={profile.full_name || 'Avatar'} />
                <AvatarFallback>
                  {getUserInitials(profile.full_name, profile.email)}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {profile.full_name || 'Usuário'}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {profile.email}
                </p>
                <div className="flex items-center mt-1">
                  <Badge variant={profile.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                    {profile.role === 'admin' ? 'Administrador' : 'Usuário'}
                  </Badge>
                </div>
              </div>
            </DropdownMenuLabel>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem className="cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              <span>Perfil</span>
            </DropdownMenuItem>
            
            <DropdownMenuItem className="cursor-pointer">
              <Settings className="mr-2 h-4 w-4" />
              <span>Configurações</span>
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem 
              className="cursor-pointer text-red-600 focus:text-red-600"
              onClick={handleSignOut}
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Sair</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};
